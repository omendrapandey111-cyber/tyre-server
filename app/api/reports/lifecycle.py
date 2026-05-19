# app/api/reports/tyre_lifecycle.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from app.db.deps import get_db
from app.auth.dependencies import get_current_user

from app.models.new_tyre_grn import Tyre, NewGRN
from app.models.issue_receipt import IssueReceipt
from app.models.transaction import Transaction, TransactionDetail


def clean_grn_type(grn_type: str) -> str:
    """Clean GRNType enum values for better readability"""
    if not grn_type:
        return ""
    # Remove GRNType. prefix if present
    cleaned = str(grn_type).replace("GRNType.", "").replace("GRNType_", "")
    # Replace underscores with spaces and capitalize
    cleaned = cleaned.replace("_", " ").strip()
    return cleaned.title() if cleaned else ""

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

def _make_ist(dt):
    """Convert UTC datetime to IST and make it timezone-naive for Excel"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    ist_dt = dt.astimezone(IST)
    # Remove timezones
    return ist_dt.replace(tzinfo=None)

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
            "Created By": grn.created_by,
            "Created At": _make_ist(grn.created_at)
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
            "Created By": ir.created_by,
            "Created At": _make_ist(ir.created_at)
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
            "Created By": trans.created_by,
            "Created At": _make_ist(trans.created_at)
        })

    # Sort Chronologically
    def get_sort_key(e):
        created_at = e.get("Created At")
        if created_at is None: return datetime.min
        return created_at 
    
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
                        "Outer NSD", "Removal Reason", "NSD", "KM Run", "Created By", "Created At"]
        
        df = df[[col for col in column_order if col in df.columns]]


    # ==================== EXCEL EXPORT ====================
    output = BytesIO()

    sheet_name = f"Tyre Lifecycle - {tyre_no}"
    base_name = f"Tyre_Lifecycle_{tyre_no}"

    #Create Workbook manually
    wb = Workbook()
    ws = wb.active
    ws.title = "Lifecycle_Report"

    # Write Header
    ws['A1'] = "Report Name :"
    ws['B1'] = sheet_name

    ws['A2'] = "Generated Date :"
    ws['B2'] = datetime.now(IST).replace(tzinfo=None)

    ws['A3'] = "Generated By :"
    ws['B3'] = getattr(current_user, 'full_name', None) or getattr(current_user, 'username', 'System')

    # Add blank row for spacing
    ws.append([])

    # Write DataFrame below header
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    wb.save(output)

    output.seek(0)

    now_ist = datetime.now(IST).replace(tzinfo=None)
    filename = f"{base_name}_{now_ist.strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )