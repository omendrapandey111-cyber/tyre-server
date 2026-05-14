# app/api/reports/tyre_lifecycle.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import date
import pandas as pd
from io import BytesIO

from app.db.deps import get_db
from app.auth.dependencies import get_current_user

from app.models.new_tyre_grn import Tyre, NewGRN
from app.models.issue_receipt import IssueReceipt
from app.models.transaction import Transaction, TransactionDetail

router = APIRouter()

def clean_grn_type(grn_type: str) -> str:
    """Clean GRNType enum values for better readability"""
    if not grn_type:
        return ""
    # Remove GRNType. prefix if present
    cleaned = str(grn_type).replace("GRNType.", "").replace("GRNType_", "")
    # Replace underscores with spaces and capitalize
    cleaned = cleaned.replace("_", " ").strip()
    return cleaned.title() if cleaned else ""


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

    events: List[Dict] = []

    # 1. New GRN / Purchase Entry
    tyre = db.query(Tyre).filter(Tyre.tyre_no == tyre_no).first()
    if tyre and tyre.grn:
        grn: NewGRN = tyre.grn
        grn_type_clean = clean_grn_type(grn.type)
        events.append({
            "Date": grn.grn_date,
            "Event Type": "New GRN",
            "Reference No": grn.grn_no,
            "Action": f"Purchased - {grn_type_clean}",
            "Vehicle No": "",
            "GRN Type": grn_type_clean,
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
            "Event Type": ir.action_type,                    
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
        event_type_clean = clean_grn_type(trans.grn_type)
        action_clean = event_type_clean or "Transaction"
        events.append({
            "Date": trans.date,
            "Event Type": event_type_clean,                 
            "Reference No": trans.grn_no,
            "Action": action_clean,
            "Vehicle No": td.vehicle_no or "",
            "GRN Type": event_type_clean,
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

    # Sort Chronologically
    def get_sort_key(e):
        dt = e.get("Date")
        return dt if dt is not None else date.min
    
    events.sort(key=get_sort_key)

    #apply date filters
    if date_from:
        events = [e for e in events if e["Date"] and e["Date"] >= date_from]
    if date_to:
        events = [e for e in events if e["Date"] and e["Date"] <= date_to]

    #create dataframes
    if not events:
        df = pd.DataFrame([{"Message": f"No lifecycle history for tyre number {tyre_no} "}])
    else:
        df = pd.DataFrame(events)
        #reorder columns
        column_order = ["Date", "Event Type", "Reference No", "Action", 
                        "Vehicle No", "GRN Type", "Brand", "Size", "Amount", 
                        "Status", "Remarks", "Wheel Position", "Average NSD", 
                        "Outer NSD", "Removal Reason", "NSD", "KM Run"]
        
        df = df[[col for col in column_order if col in df.columns]]


    # ==================== EXCEL EXPORT ====================
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl', datetime_format='yyyy-mm-dd') as writer:
        df.to_excel(writer, index=False, sheet_name="Tyre_Lifecycle")

    output.seek(0)

    filename = f"{tyre_no}_Tyre_Lifecycle_{date.today().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )