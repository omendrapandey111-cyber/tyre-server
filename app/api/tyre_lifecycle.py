from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from app.db.deps import get_db
from app.schemas.lifecycle import TyreLifecycleResponse, TyreLifecycleEvent

from app.models.new_tyre_grn import Tyre, NewGRN
from app.models.issue_receipt import IssueReceipt
from app.models.transaction import Transaction, TransactionDetail

router = APIRouter(prefix="/tyre", tags=["Tyre Lifecycle"])


def clean_grn_type(grn_type) -> str:
    if not grn_type:
        return ""
    cleaned = str(grn_type).replace("GRNType.", "").replace("GRNType_", "")
    cleaned = cleaned.replace("_", " ").strip()
    return cleaned.title()


@router.get("/{tyre_no}/lifecycle", response_model=TyreLifecycleResponse)
def get_tyre_lifecycle(
    tyre_no: str,
    db: Session = Depends(get_db)
):
    tyre = db.query(Tyre).filter(Tyre.tyre_no == tyre_no).first()
    if not tyre:
        raise HTTPException(status_code=404, detail=f"Tyre {tyre_no} not found")

    events = []

    # ====================== 1. New GRN / Purchase ======================
    if tyre.grn:
        grn: NewGRN = tyre.grn
        events.append({
            "date": grn.grn_date,
            "event_type": "New GRN",
            "reference_no": grn.grn_no,
            "action": f"Purchased - {clean_grn_type(grn.type)}",
            "vehicle_no": None,
            "grn_type": clean_grn_type(grn.type),
            "brand": tyre.brand,
            "size": tyre.size,
            "amount": tyre.total_amt,
            "status": tyre.current_status,
            "remarks": grn.remark,
            "created_by": grn.created_by,
            "created_at": grn.created_at,
        })

    # ====================== 2. Issue & Receipt ======================
    ir_records = db.query(IssueReceipt)\
        .filter(IssueReceipt.tyre_no == tyre_no)\
        .order_by(IssueReceipt.ir_date, IssueReceipt.created_at).all()

    for ir in ir_records:
        events.append({
            "date": ir.ir_date,
            "event_type": ir.action_type,
            "reference_no": ir.ir_no,
            "action": f"{ir.action_type} - {ir.status}",
            "vehicle_no": ir.vehicle_no,
            "wheel_position": ir.wheel_position,
            "status": ir.status,
            "remarks": ir.remarks or ir.removal_reason,
            "removal_reason": ir.removal_reason,
            "average_nsd": ir.average_nsd,
            "outer_nsd": ir.outer_nsd,
            "created_by": ir.created_by,
            "created_at": ir.created_at,
        })

    # ====================== 3. Transactions (Send/Receive/Scrap etc.) ======================
    trans_details = db.query(TransactionDetail)\
        .join(Transaction, Transaction.grn_no == TransactionDetail.grn_no)\
        .filter(TransactionDetail.tyre_no == tyre_no)\
        .order_by(Transaction.date, TransactionDetail.id).all()

    for td in trans_details:
        trans = td.transaction
        event_type_clean = clean_grn_type(trans.grn_type)

        events.append({
            "date": trans.date,
            "event_type": event_type_clean or "Transaction",
            "reference_no": trans.grn_no,
            "action": event_type_clean or "Transaction",
            "vehicle_no": td.vehicle_no,
            "grn_type": event_type_clean,
            "nsd": td.nsd,
            "km_run": td.km_run,
            "remarks": td.remark or trans.remark_reason,
            "created_by": trans.created_by,
            "created_at": trans.created_at,
        })

    # ====================== Sort Chronologically ======================
    events.sort(key=lambda x: (x["created_at"] or x["date"], x["reference_no"]))

    # Convert to Pydantic models
    pydantic_events = [TyreLifecycleEvent(**e) for e in events]

    return TyreLifecycleResponse(
        tyre_no=tyre_no,
        brand=tyre.brand,
        size=tyre.size,
        total_events=len(pydantic_events),
        events=pydantic_events
    )