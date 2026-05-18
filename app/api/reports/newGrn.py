
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

from app.models.new_tyre_grn import NewGRN, Tyre   


class GRNTypeFilter(str, Enum):
    ALL = "All"
    NEW = "New"
    NEW_REMOULD = "New-Remould"
    CHASSIS = "Chassis"


def _make_naive(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt


router = APIRouter()


@router.get("/new-grn-report", summary="Download New GRN / Tyre Purchase Report")
def get_new_grn_report(
    date_from: Optional[date] = Query(None, description="Start Date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End Date (YYYY-MM-DD)"),
    grn_type: GRNTypeFilter = Query(GRNTypeFilter.ALL, description="GRN Type"),
    tyre_no: Optional[str] = Query(None, description="Tyre Number"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Base query on NewGRN
    query = db.query(NewGRN)

    # Filter by GRN Type
    if grn_type != GRNTypeFilter.ALL:
        query = query.filter(NewGRN.type == grn_type.value)

    # Date filtering on GRN Date
    if date_from:
        query = query.filter(NewGRN.grn_date >= date_from)
    if date_to:
        query = query.filter(NewGRN.grn_date <= date_to)

    # If tyre_no is provided, join with tyres
    if tyre_no:
        query = query.join(NewGRN.tyres).filter(Tyre.tyre_no.ilike(f"%{tyre_no}%"))

    # Get results
    grns = query.order_by(NewGRN.grn_date.desc()).all()

    report_data = []

    for grn in grns:
        for tyre in grn.tyres:   # Loop through all tyres in this GRN
            if tyre_no and tyre_no.lower() not in tyre.tyre_no.lower():
                continue

            report_data.append({
                # GRN Header Information
                "GRN No": grn.grn_no,
                "GRN Date": grn.grn_date,
                "GRN Type": grn.type,
                "Office ID": grn.office_id,
                "Vendor ID": grn.vendor_id,
                "Vendor Office": grn.vendor_office,
                "Challan No": grn.challan_no,
                "Challan Date": grn.challan_date,
                "Total Tyres": grn.total_tyre_count,
                "Total Amount": grn.total_amount,
                "Total GST": grn.total_gst,
                "Total Discount": grn.total_discount,
                "Remark": grn.remark,
                "Created By": grn.created_by,
                "Created At": _make_naive(grn.created_at),

                # Tyre Details
                "Tyre No": tyre.tyre_no,
                "Brand": tyre.brand,
                "Size": tyre.size,
                "Production Month": tyre.production_month,
                "Rubber Brand": tyre.rubber_brand,
                "Rubber Type": tyre.rubber_type,
                "Amount": tyre.amount,
                "Discount": tyre.discount,
                "CGST": tyre.cgst,
                "SGST": tyre.sgst,
                "IGST": tyre.igst,
                "Total GST (Tyre)": tyre.total_gst,
                "Total Amount (Tyre)": tyre.total_amt,
                "Current Status": tyre.current_status,
            })

    # ==================== EXCEL EXPORT ====================
    df = pd.DataFrame(report_data)
    output = BytesIO()

    # Dynamic sheet name & filename
    if grn_type == GRNTypeFilter.ALL:
        sheet_name = "All_New_GRN"
        base_name = "New_GRN_Report"
    else:
        sheet_name = f"{grn_type.value}_GRN"
        base_name = f"{grn_type.value}_GRN_Report"

    with pd.ExcelWriter(output, engine='openpyxl', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    output.seek(0)

    filename = f"{base_name}_{date.today().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )