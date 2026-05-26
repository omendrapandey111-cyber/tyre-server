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
    if not grn_type:
        return ""
    cleaned = str(grn_type).replace("GRNType.", "").replace("GRNType_", "")
    cleaned = cleaned.replace("_", " ").strip()
    return cleaned.title() if cleaned else ""


IST = timezone(timedelta(hours=5, minutes=30))

def _make_ist(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(IST)
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

    # 3. Transactions
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
        if created_at is None:
            return datetime.min
        return created_at

    events.sort(key=get_sort_key)

    # Apply date filters
    if date_from:
        events = [e for e in events if e["Date"] and e["Date"] >= date_from]
    if date_to:
        events = [e for e in events if e["Date"] and e["Date"] <= date_to]

    # Build DataFrame
    if not events:
        df = pd.DataFrame([{"Message": f"No lifecycle history found for tyre {tyre_no}"}])
    else:
        df = pd.DataFrame(events)
        column_order = [
            "Date", "Event Type", "Reference No", "Action",
            "Vehicle No", "GRN Type", "Brand", "Size", "Amount",
            "Status", "Remarks", "Wheel Position", "Average NSD",
            "Outer NSD", "Removal Reason", "NSD", "KM Run",
            "Created By", "Created At"
        ]
        df = df[[col for col in column_order if col in df.columns]]

    output = BytesIO()
    base_name = f"Tyre_Lifecycle_{tyre_no}"
    report_name = f"Tyre Lifecycle - {tyre_no}"

    generated_at = datetime.now(IST).replace(tzinfo=None)
    generated_by = getattr(current_user, 'full_name', None) or getattr(current_user, 'username', '')

    wb = Workbook()

    # ── SUMMARY SHEET ──────────────────────────────────────────────
    summary_ws = wb.active
    summary_ws.title = "Summary"

    # Pull tyre-level metadata for summary (if tyre exists)
    tyre_brand = tyre.brand if tyre else ""
    tyre_size  = tyre.size  if tyre else ""
    tyre_status = tyre.current_status if tyre else ""

    summary_data = [
        ["Report Name",    report_name],
        ["Generated At",   generated_at],
        ["Generated By",   generated_by],
        ["Tyre No",        tyre_no],
        ["Tyre Brand",     tyre_brand],
        ["Tyre Size",      tyre_size],
        ["Current Status", tyre_status],
        ["From Date",      date_from if date_from else ""],
        ["To Date",        date_to   if date_to   else ""],
        ["Total Events",   len(events)],
    ]

    for row in summary_data:
        summary_ws.append(row)

    for col in summary_ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        summary_ws.column_dimensions[col_letter].width = min(max_length + 5, 50)

    # ── LIFECYCLE REPORT SHEET ─────────────────────────────────────
    report_ws = wb.create_sheet(title="Lifecycle_Report")

    if df.empty or (len(df.columns) == 1 and "Message" in df.columns):
        report_ws.append(["No lifecycle history found for tyre " + tyre_no])
    else:
        for r in dataframe_to_rows(df, index=False, header=True):
            report_ws.append(r)

    for col in report_ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        report_ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

    wb.save(output)
    output.seek(0)

    now_ist = datetime.now(IST).replace(tzinfo=None)
    filename = f"{base_name}_{now_ist.strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )