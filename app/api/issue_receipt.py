from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.deps import get_db_tyre as get_db
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


def get_latest_position_record(db: Session, vehicle_no: str, position: str):
    return db.query(TyrePosition)\
        .filter(
            TyrePosition.vehicle_no == vehicle_no,
            TyrePosition.position == position,
        )\
        .order_by(TyrePosition.created_at.desc(), TyrePosition.id.desc())\
        .first()


def get_latest_tyre_record(db: Session, vehicle_no: str, tyre_no: str):
    return db.query(TyrePosition)\
        .filter(
            TyrePosition.vehicle_no == vehicle_no,
            TyrePosition.tyre_no == tyre_no,
        )\
        .order_by(TyrePosition.created_at.desc(), TyrePosition.id.desc())\
        .first()


def is_position_occupied(db: Session, vehicle_no: str, position: str) -> bool:
    latest = get_latest_position_record(db, vehicle_no, position)

    if not latest:
        return False  # never used → free

    return latest.event_type == "Issue"


def validate_position(layout, position):
    if not layout or "tyres" not in layout:
        raise HTTPException(500, "Invalid layout structure")

    valid = [t["position"] for t in layout["tyres"]]

    if position not in valid:
        raise HTTPException(400, f"Invalid position {position}")


# ================= MAIN API =================

@router.post("/", status_code=201)
def create_issue_receipt(data: IssueReceiptCreate, db: Session = Depends(get_db)):

    try:
        action_type = data.action_type

        # 1. Validate Office
        if not db.query(Office).filter(Office.id == data.office_id).first():
            raise HTTPException(404, "Office not found")

        # 2. Validate Layout
        layout_obj = db.query(TyreLayout).filter(TyreLayout.id == data.layout_id).first()
        if not layout_obj:
            raise HTTPException(404, "Layout not found")

        layout = layout_obj.layout

        ir_date = data.ir_date or date.today()
        ir_no = generate_ir_no(db, action_type, ir_date)

        results = []

        for item in data.details:

            tyre = db.query(Tyre).filter(Tyre.tyre_no == item.tyre_no).first()
            if not tyre:
                raise HTTPException(404, f"Tyre {item.tyre_no} not found")

            # ================= ISSUE =================
            if action_type == "Issue":

                if not item.wheel_position:
                    raise HTTPException(400, "wheel_position required")

                validate_position(layout, item.wheel_position)

                if is_position_occupied(db, data.vehicle_no, item.wheel_position):
                    latest = get_latest_position_record(db, data.vehicle_no, item.wheel_position)

                    raise HTTPException(
                        400,
                        f"Position {item.wheel_position} already occupied by tyre {latest.tyre_no}. Perform receipt first."
                    )

                ir_entry = IssueReceipt(
                    ir_no=ir_no,
                    action_type="Issue",
                    ir_date=ir_date,
                    office_id=data.office_id,
                    vehicle_no=data.vehicle_no,
                    vehicle_km=data.vehicle_km,
                    tyre_no=item.tyre_no,
                    wheel_position=item.wheel_position,
                    removal_reason=None,   #not required for issue
                    status="On Vehicle",
                    created_by=data.created_by,
                )

                db.add(ir_entry)
                db.flush()

                db.add(TyrePosition(
                    vehicle_no=data.vehicle_no,
                    layout_id=data.layout_id,
                    tyre_no=item.tyre_no,
                    position=item.wheel_position,
                    event_type="Issue",
                    reference_ir_id=ir_entry.id,
                    created_by=data.created_by
                ))

                tyre.vehicle_no = data.vehicle_no
                tyre.status = "On Vehicle"
                tyre.current_status = "On Vehicle"

                db.add(tyre)
                results.append(ir_entry)

            # ================= RECEIPT =================
            elif action_type == "Receipt":

                latest = get_latest_tyre_record(db, data.vehicle_no, item.tyre_no)

                if not latest or latest.event_type != "Issue":
                    raise HTTPException(
                        400,
                        f"Tyre {item.tyre_no} is not currently on vehicle"
                    )

                ir_entry = IssueReceipt(
                    ir_no=ir_no,
                    action_type="Receipt",
                    ir_date=ir_date,
                    office_id=data.office_id,
                    vehicle_no=data.vehicle_no,
                    vehicle_km=data.vehicle_km,
                    tyre_no=item.tyre_no,
                    wheel_position=latest.position,
                    removal_reason=item.removal_reason,
                    status="Off Vehicle",
                    created_by=data.created_by,
                )

                db.add(ir_entry)
                db.flush()

                db.add(TyrePosition(
                    vehicle_no=data.vehicle_no,
                    layout_id=data.layout_id,
                    tyre_no=item.tyre_no,
                    position=latest.position,
                    event_type="Receipt",
                    reference_ir_id=ir_entry.id,
                    created_by=data.created_by
                ))

                tyre.vehicle_no = None
                tyre.status = "Off Vehicle"
                tyre.current_status = item.removal_reason

                db.add(tyre)
                results.append(ir_entry)

        db.commit()

        return {
            "message": "Transaction successful",
            "ir_no": ir_no,
            "count": len(results),
        }

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ================= GET ALL =================

@router.get("/")
def get_all_issue_receipts(db: Session = Depends(get_db)):
    return db.query(IssueReceipt)\
        .order_by(IssueReceipt.created_at.desc())\
        .all()