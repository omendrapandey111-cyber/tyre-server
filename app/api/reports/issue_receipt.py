from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import pandas as pd
from io import BytesIO
from enum import Enum

from app.db.deps import get_db
from app.auth.dependencies import get_current_user

from app.models import issue_receipt as issue_receipt_model
from app.models.new_tyre_grn import Tyre


class ActionTypeFilter(str, Enum):
    ALL = "All"
    ISSUE = "Issue"
    RECEIPT = "Receipt"


def _make_naive(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt


router = APIRouter()


@router.get("/issue-receipt-report", summary="Download Issue & Receipt Excel Report")
def get_issue_receipt_report(
    date_from: Optional[date] = Query(None, description="Start Date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End Date (YYYY-MM-DD)"),
    vehicle_no: Optional[str] = Query(None, description="Vehicle Number"),
    tyre_no: Optional[str] = Query(None, description="Tyre Number"),
    action_type: ActionTypeFilter = Query(ActionTypeFilter.ALL, description="Select Report Type"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(issue_receipt_model.IssueReceipt)

    # Filter by Action Type
    if action_type != ActionTypeFilter.ALL:
        query = query.filter(
            issue_receipt_model.IssueReceipt.action_type == action_type.value
        )

    if date_from:
        query = query.filter(issue_receipt_model.IssueReceipt.ir_date >= date_from)
    if date_to:
        query = query.filter(issue_receipt_model.IssueReceipt.ir_date <= date_to)
    if vehicle_no:
        query = query.filter(issue_receipt_model.IssueReceipt.vehicle_no.ilike(f"%{vehicle_no}%"))
    if tyre_no:
        query = query.filter(issue_receipt_model.IssueReceipt.tyre_no.ilike(f"%{tyre_no}%"))
        
    results = query.order_by(issue_receipt_model.IssueReceipt.ir_date.desc()).all()

    report_data = []
    for ir in results:
        tyre = db.query(Tyre).filter(Tyre.tyre_no == ir.tyre_no).first() if ir.tyre_no else None

        report_data.append({
            "IR No": ir.ir_no,
            "Action Type": ir.action_type,
            "IR Date": ir.ir_date,
            "Office ID": ir.office_id,
            "Vehicle No": ir.vehicle_no,
            "Vehicle KM": ir.vehicle_km,
            "Tyre No": ir.tyre_no,

            # Receipt Fields
            "Convert to Stepney": ir.convert_to_stepney,
            "Outer NSD": ir.outer_nsd,
            "Center NSD": ir.center_nsd,
            "Center2 NSD": ir.center2_nsd,
            "Inner NSD": ir.inner_nsd,
            "Average NSD": ir.average_nsd,

            # Issue Fields
            "Issue to Stepney": ir.issue_to_stepney,
            "Wheel Position": ir.wheel_position,
            "Remarks": ir.remarks,
            "Removal Reason": ir.removal_reason,

            "Status": ir.status,
            "Created By": ir.created_by,
            "Created At": _make_naive(ir.created_at),

            # Tyre Information
            "Tyre Brand": tyre.brand if tyre else None,
            "Tyre Size": tyre.size if tyre else None,
            "Production Month": tyre.production_month if tyre else None,
            "Tyre GRN No": tyre.grn_no if tyre else None,
            "Tyre Current Status": tyre.current_status if tyre else None,
        })

    #Excel Report Generation
    df = pd.DataFrame(report_data)
    output = BytesIO()

    # Dynamic Sheet Name
    if action_type == ActionTypeFilter.ISSUE:
        sheet_name = "Issue_Report"
        base_name = "Issue_Report"
    elif action_type == ActionTypeFilter.RECEIPT:
        sheet_name = "Receipt_Report"
        base_name = "Receipt_Report"
    else:
        sheet_name = "Issue_Receipt_Full_Report"
        base_name = "Issue_Receipt_Report"

    with pd.ExcelWriter(output, engine='openpyxl', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    output.seek(0)

    filename = f"{base_name}_{date.today().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )