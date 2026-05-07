# app/api/reports/tyre_lifecycle.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import pandas as pd
from io import BytesIO

from app.db.deps import get_db
from app.auth.dependencies import get_current_user

from app.models.new_tyre_grn import Tyre, NewGRN
from app.models.issue_receipt import IssueReceipt
from app.models.transaction import Transaction, TransactionDetail

router = APIRouter()


@router.get("/tyre-lifecycle-report", summary="Tyre Complete Lifecycle Report")
def get_tyre_lifecycle_report(
    tyre_no: str = Query(..., description="Tyre Number (Required)"),
    date_from: Optional[date] = Query(None, description="Start Date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End Date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not tyre_no or tyre_no.strip() == "":
        raise HTTPException(status_code=400, detail="tyre_no is required")

    events = []

    # 1. New GRN / Purchase Entry
    tyre = db.query(Tyre).filter(Tyre.tyre_no == tyre_no).first()
    if tyre and tyre.grn:
        grn = tyre.grn
        events.append({
            "Date": grn.grn_date,
            "Event Type": "New GRN",
            "Reference No": grn.grn_no,
            "Action": f"Purchased - {grn.type}",
            "Vehicle No": "",
            "GRN Type": grn.type,
            "Brand": tyre.brand,
            "Size": tyre.size,
            "Amount": tyre.total_amt,
            "Status": tyre.current_status,
            "Remarks": grn.remark,
            "NSD": "",
            "KM Run": "",
        })

    # 2. Issue & Receipt History
    ir_records = db.query(IssueReceipt).filter(
        IssueReceipt.tyre_no == tyre_no
    ).order_by(IssueReceipt.ir_date).all()

    for ir in ir_records:
        events.append({
            "Date": ir.ir_date,
            "Event Type": ir.action_type,                    # "Issue" or "Receipt"
            "Reference No": ir.ir_no,
            "Action": f"{ir.action_type} - {ir.status}",
            "Vehicle No": ir.vehicle_no,
            "GRN Type": "",
            "Brand": "",
            "Size": "",
            "Amount": "",
            "Status": ir.status,
            "Remarks": ir.remarks or ir.removal_reason or "",
            "Wheel Position": ir.wheel_position,
            "Average NSD": ir.average_nsd,
            "Outer NSD": ir.outer_nsd,
            "Removal Reason": ir.removal_reason,
            "NSD": "",
            "KM Run": "",
        })

    # 3. Transactions (Send-Remould, Scrap, Claim, etc.)
    trans_details = db.query(TransactionDetail).filter(
        TransactionDetail.tyre_no == tyre_no
    ).join(Transaction).order_by(Transaction.date).all()

    for td in trans_details:
        trans = td.transaction
        events.append({
            "Date": trans.date,
            "Event Type": trans.grn_type,                    # ← Changed: Shows actual type (Send-Remould, Scrap, etc.)
            "Reference No": trans.grn_no,
            "Action": trans.grn_type,
            "Vehicle No": td.vehicle_no or "",
            "GRN Type": trans.grn_type,
            "Brand": "",
            "Size": "",
            "Amount": "",
            "Status": "",
            "Remarks": td.remark or trans.remark_reason or "",
            "Wheel Position": "",
            "Average NSD": "",
            "Outer NSD": "",
            "Removal Reason": "",
            "NSD": td.nsd,
            "KM Run": td.km_run,
        })

    # Sort chronologically
    events.sort(key=lambda x: x["Date"] or date.min)

    # Apply date filter
    if date_from:
        events = [e for e in events if e["Date"] and e["Date"] >= date_from]
    if date_to:
        events = [e for e in events if e["Date"] and e["Date"] <= date_to]

    if not events:
        df = pd.DataFrame([{"Message": f"No lifecycle history found for tyre: {tyre_no}"}])
    else:
        df = pd.DataFrame(events)

    # ==================== EXCEL EXPORT ====================
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl', datetime_format='yyyy-mm-dd') as writer:
        df.to_excel(writer, index=False, sheet_name="Tyre_Lifecycle")

    output.seek(0)

    filename = f"Tyre_Lifecycle_{date.today().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )