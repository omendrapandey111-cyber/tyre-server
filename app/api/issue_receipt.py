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


def get_active_position(db, vehicle_no, position):
    return db.query(TyrePosition)\
        .filter(
            TyrePosition.vehicle_no == vehicle_no,
            TyrePosition.position == position,
        ).first()


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

        #CREATE ISSUE RECEIPT
        ir_entry = IssueReceipt(
            ir_no=ir_no,
            action_type=data.action_type.value,
            ir_date=ir_date,
            office_id=data.office_id,
            vehicle_no=data.vehicle_no,
            vehicle_km=data.vehicle_km,
            tyre_no=item.tyre_no,

            convert_to_stepney=item.convert_to_stepney,
            outer_nsd=item.outer_nsd,
            center_nsd=item.center_nsd,
            center2_nsd=item.center2_nsd,
            inner_nsd=item.inner_nsd,
            average_nsd=item.average_nsd,

            issue_to_stepney=item.issue_to_stepney,
            wheel_position=item.wheel_position,
            remarks=item.remarks,

            status=final_status,
            created_by=data.created_by,
        )

        db.add(ir_entry)
        db.flush()

        #POSITION LOGIC 

        if data.action_type == "Issue":

            if not item.wheel_position:
                raise HTTPException(400, "wheel_position required")

            validate_position(layout, item.wheel_position)

            existing = get_active_position(db, data.vehicle_no, item.wheel_position)

            #REPLACEMENT CASE (remove old tyre first)
            if existing and existing.tyre_no is not None:

                old_tyre = db.query(Tyre)\
                    .filter(Tyre.tyre_no == existing.tyre_no)\
                    .first()

                if old_tyre:
                    old_tyre.vehicle_no = None
                    old_tyre.status = "Off Vehicle"

                # log removal
                db.add(TyrePosition(
                    vehicle_no=data.vehicle_no,
                    layout_id=data.layout_id,
                    tyre_no=existing.tyre_no,
                    position=item.wheel_position,
                    event_type="REPLACE_REMOVE",
                    reference_ir_id=ir_entry.id,
                    created_by=data.created_by
                ))

            #ADD NEW TYRE
            db.add(TyrePosition(
                vehicle_no=data.vehicle_no,
                layout_id=data.layout_id,
                tyre_no=item.tyre_no,
                position=item.wheel_position,
                event_type="ISSUE",
                reference_ir_id=ir_entry.id,
                created_by=data.created_by
            ))

            # UPDATE TYRE MASTER
            tyre.vehicle_no = data.vehicle_no
            tyre.status = "On Vehicle"

        # RECEIPT

        elif data.action_type == "Receipt":

            current = db.query(TyrePosition)\
                .filter(
                    TyrePosition.vehicle_no == data.vehicle_no,
                    TyrePosition.tyre_no == item.tyre_no,
                )\
                .first()

            if not current:
                raise HTTPException(400, f"Tyre {item.tyre_no} not on vehicle")

            db.add(TyrePosition(
                vehicle_no=data.vehicle_no,
                layout_id=data.layout_id,
                tyre_no=item.tyre_no,
                position=current.position,
                event_type="RECEIPT",
                reference_ir_id=ir_entry.id,
                created_by=data.created_by
            ))

            # UPDATE TYRE MASTER
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


# Get All Issue/Receipt records

@router.get("/")
def get_all_issue_receipts(db: Session = Depends(get_db)):
    return db.query(IssueReceipt)\
        .order_by(IssueReceipt.created_at.desc())\
        .all()