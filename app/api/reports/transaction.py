from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from io import BytesIO
from enum import Enum

from app.db.deps import get_db
from app.auth.dependencies import get_current_user

from app.models import transaction as transaction_model   
from app.models.new_tyre_grn import Tyre
from app.models.fleet_vendor import FleetVendor
from app.models.office import Office

#Enums for dropdown filters
class GRNTypeFilter(str, Enum):
    ALL = "All"
    SEND_REMOULD = "Send-Remould"
    SEND_CLAIM = "Send-Claim"
    SCRAP = "Scrap"
    RESELL = "Resell"
    THEFT = "Theft"
    RECEIVE_REMOULD = "Receive-Remould"
    RECEIVE_CLAIM = "Receive-Claim"

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

@router.get("/transaction-report", summary="Download Transaction Excel Report")
def get_transaction_report(
    date_from: Optional[date] = Query(None, description="Start Date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End Date (YYYY-MM-DD)"),
    grn_type: GRNTypeFilter = Query(GRNTypeFilter.ALL, description="Select GRN Type"),
    tyre_no: Optional[str] = Query(None, description="Tyre Number"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(transaction_model.Transaction)

    # Filter by GRN Type
    if grn_type != GRNTypeFilter.ALL:
        query = query.filter(
            transaction_model.Transaction.grn_type == grn_type.value)

    if date_from:
        query = query.filter(transaction_model.Transaction.date >= date_from)
    if date_to:
        query = query.filter(transaction_model.Transaction.date <= date_to)

    if tyre_no:
        query = query.join(transaction_model.TransactionDetail).filter(
            transaction_model.TransactionDetail.tyre_no.ilike(f"%{tyre_no}%")
        )
    
    transactions = query.order_by(transaction_model.Transaction.date.desc()).all()

    report_data = []
    for trans in transactions:
        #fetch office  details
        office = db.query(Office).filter(Office.id == trans.office_id).first()
        office_name = office.name if office else trans.office_id

        #fetch vendor details
        vendor = db.query(FleetVendor).filter(FleetVendor.id == trans.vendor_id).first()
        vendor_name = vendor.name if vendor else (trans.vendor_id or "N/A")

        for detail in trans.details:
            tyre = db.query(Tyre).filter(Tyre.tyre_no == detail.tyre_no).first() if detail.tyre_no else None

            #clean grn display name
            grn_type_display = trans.grn_type
            if isinstance(grn_type_display, Enum):
                grn_type_display = grn_type_display.value

            report_data.append({
                "GRN No": trans.grn_no,
                "GRN Type": grn_type_display,
                "Transaction Date": trans.date,
                "Office Name": office_name,
                "Vendor Name": vendor_name,
                "Total Tyres": trans.total_tyres,
                "Total Amount": trans.total_amount,
                "Remark / Reason": trans.remark_reason,
                "Place": trans.place,
                "Created By": trans.created_by,
                "Created At": _make_ist(trans.created_at),

                "Tyre No": detail.tyre_no,
                "Vehicle No": detail.vehicle_no,
                "Reason": detail.reason,
                "NSD": detail.nsd,
                "KM Run": detail.km_run,
                "Detail Remark": detail.remark,

                "Tyre Brand": tyre.brand if tyre else None,
                "Tyre Size": tyre.size if tyre else None,
                "Production Month": tyre.production_month if tyre else None,
                "Tyre Current Status": tyre.current_status if tyre else None,
            })

    # Excel Generation
    df = pd.DataFrame(report_data)
    output = BytesIO()

    if grn_type == GRNTypeFilter.ALL:
        sheet_name = "All_Transactions"
        base_name = "Transaction_Report"
    else:
        sheet_name = f"{grn_type.value}_Report"
        base_name = f"{grn_type.value}_Report"

    with pd.ExcelWriter(output, engine='openpyxl', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    output.seek(0)

    now = datetime.now()
    filename = f"{base_name}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )