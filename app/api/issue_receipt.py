# app/api/issue_receipt.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.deps import get_db
from app.models.issue_receipt import IssueReceipt
from app.models.new_tyre_grn import Tyre
from app.models.tyre_position import TyrePosition
from app.models.tyre_layouts import TyreLayout
from app.models.office import Office

from app.schemas.issue_receipt import IssueReceiptCreate

router = APIRouter(prefix="/issue-receipt", tags=["Issue / Receipt"])


# ================= HELPERS =================

def generate_ir_no(db: Session, action_type: str, ir_date: date) -> str:
    prefix = "IR" if action_type == "Issue" else "RR"
    date_str = ir_date.strftime("%d%m%y")

    last = db.query(IssueReceipt.ir_no)\
        .filter(IssueReceipt.ir_no.like(f"{prefix}-{date_str}-%"))\
        .order_by(IssueReceipt.ir_no.desc())\
        .first()

    seq = int(last[0].split("-")[-1]) + 1 if last else 1
    return f"{prefix}-{date_str}-{seq:06d}"


def get_latest_position(db, vehicle_no, position):
    return db.query(TyrePosition)\
        .filter(
            TyrePosition.vehicle_no == vehicle_no,
            TyrePosition.position == position,
        )\
        .order_by(TyrePosition.created_at.desc())\
        .first()


def get_latest_tyre_record(db, vehicle_no, tyre_no):
    return db.query(TyrePosition)\
        .filter(
            TyrePosition.vehicle_no == vehicle_no,
            TyrePosition.tyre_no == tyre_no,
        )\
        .order_by(TyrePosition.created_at.desc())\
        .first()


def validate_position(layout, position):
    valid = [t["position"] for t in layout["tyres"]]
    if position not in valid:
        raise HTTPException(400, f"Invalid position {position}")


# ================= MAIN API =================

@router.post("/", status_code=201)
def create_issue_receipt(data: IssueReceiptCreate, db: Session = Depends(get_db)):

    # 1. Validate Office
    if not db.query(Office).filter(Office.id == data.office_id).first():
        raise HTTPException(404, "Office not found")

    # 2. Validate Layout
    layout_obj = db.query(TyreLayout).filter(TyreLayout.id == data.layout_id).first()
    if not layout_obj:
        raise HTTPException(404, "Layout not found")

    layout = layout_obj.layout

    ir_date = data.ir_date or date.today()
    ir_no = generate_ir_no(db, data.action_type.value, ir_date)

    results = []

    for item in data.details:

        tyre = db.query(Tyre).filter(Tyre.tyre_no == item.tyre_no).first()
        if not tyre:
            raise HTTPException(404, f"Tyre {item.tyre_no} not found")

        final_status = "On Vehicle" if data.action_type == "Issue" else "Off Vehicle"

        # ================= ISSUE =================
        if data.action_type == "Issue":

            if not item.wheel_position:
                raise HTTPException(400, "wheel_position required")

            validate_position(layout, item.wheel_position)

            # Check if position already has ACTIVE tyre
            existing = get_latest_position(db, data.vehicle_no, item.wheel_position)

            if existing and existing.event_type == "ISSUE":
                # Do NOT auto-remove — frontend already handles receipt
                raise HTTPException(
                    400,
                    f"Position {item.wheel_position} already occupied. Perform receipt first."
                )

            # Create Issue Entry
            ir_entry = IssueReceipt(
                ir_no=ir_no,
                action_type="Issue",
                ir_date=ir_date,
                office_id=data.office_id,
                vehicle_no=data.vehicle_no,
                vehicle_km=data.vehicle_km,
                tyre_no=item.tyre_no,
                wheel_position=item.wheel_position,
                status="On Vehicle",
                created_by=data.created_by,
            )

            db.add(ir_entry)
            db.flush()

            # Log position
            db.add(TyrePosition(
                vehicle_no=data.vehicle_no,
                layout_id=data.layout_id,
                tyre_no=item.tyre_no,
                position=item.wheel_position,
                event_type="ISSUE",
                reference_ir_id=ir_entry.id,
                created_by=data.created_by
            ))

            # Update tyre master
            tyre.vehicle_no = data.vehicle_no
            tyre.status = "On Vehicle"

            db.add(tyre)
            results.append(ir_entry)

        # ================= RECEIPT =================

        elif data.action_type == "Receipt":

            latest = get_latest_tyre_record(db, data.vehicle_no, item.tyre_no)

            # Only allow receipt if tyre is currently ON vehicle
            if not latest or latest.event_type != "ISSUE":
                raise HTTPException(
                    400,
                    f"Tyre {item.tyre_no} is not currently on vehicle"
                )

            # Create Receipt Entry
            ir_entry = IssueReceipt(
                ir_no=ir_no,
                action_type="Receipt",
                ir_date=ir_date,
                office_id=data.office_id,
                vehicle_no=data.vehicle_no,
                vehicle_km=data.vehicle_km,
                tyre_no=item.tyre_no,
                wheel_position=latest.position,
                status="Off Vehicle",
                created_by=data.created_by,
            )

            db.add(ir_entry)
            db.flush()

            # Log receipt
            db.add(TyrePosition(
                vehicle_no=data.vehicle_no,
                layout_id=data.layout_id,
                tyre_no=item.tyre_no,
                position=latest.position,
                event_type="RECEIPT",
                reference_ir_id=ir_entry.id,
                created_by=data.created_by
            ))

            # Update tyre master
            tyre.vehicle_no = None
            tyre.status = "Off Vehicle"

            db.add(tyre)
            results.append(ir_entry)

    db.commit()

    return {
        "message": "Transaction successful",
        "count": len(results),
        "ir_no": ir_no
    }


# ================= GET ALL =================

@router.get("/")
def get_all_issue_receipts(db: Session = Depends(get_db)):
    return db.query(IssueReceipt)\
        .order_by(IssueReceipt.created_at.desc())\
        .all()