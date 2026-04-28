from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from uuid import UUID

from app.db.deps import get_db
from app.models.new_tyre_grn import NewGRN, Tyre, GRNType
from app.schemas.new_tyre_grn import NewGRNCreate, NewGRNResponse
from app.core.security import get_current_user , CurrentUser  

router = APIRouter(prefix="/new-tyre-grn", tags=["New Tyre GRN"])


def generate_grn_no(db: Session, grn_type: GRNType) -> str:
    prefix_map = {
        "New": "NW",
        "New-Remould": "NR",
        "Chassis": "CS"
    }
    prefix_code = prefix_map.get(grn_type.value if hasattr(grn_type, "value") else grn_type)
    if not prefix_code:
        raise ValueError("Invalid GRN type")

    today = date.today().strftime("%d%m%y")

    last_grn = (
        db.query(NewGRN.grn_no)
        .filter(NewGRN.grn_no.like(f"{prefix_code}-{today}-%"))
        .order_by(NewGRN.grn_no.desc())
        .first()
    )

    seq = int(last_grn[0].split("-")[-1]) + 1 if last_grn else 1
    return f"{prefix_code}-{today}-{seq:06d}"


@router.post("/", response_model=NewGRNResponse, status_code=status.HTTP_201_CREATED)
def create_new_tyre_grn(
    data: NewGRNCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # Security: User must belong to the same organization
    if current_user.org_id != data.org_id:
        raise HTTPException(status_code=403, detail="You can only create GRN for your own organization")

    grn_no = generate_grn_no(db, data.type)
    grn_date = data.grn_date or date.today()

    db_grn = NewGRN(
        grn_no=grn_no,
        grn_date=grn_date,
        org_id=data.org_id,
        zone_id=data.zone_id,
        office_id=data.office_id,
        vendor_id=data.vendor_id,
        vendor_office=data.vendor_office,
        state=data.state,
        gst_no=data.gst_no,
        challan_no=data.challan_no,
        challan_date=data.challan_date,
        remark=data.remark,
        type=data.type.value,
    )

    db.add(db_grn)
    db.commit()
    db.refresh(db_grn)

    total_tyre_count = len(data.tyres)
    total_amount = total_gst = total_discount = 0.0

    for tyre_data in data.tyres:
        tyre = Tyre(
            tyre_no=tyre_data.tyre_no,
            org_id=data.org_id,
            zone_id=data.zone_id,
            production_month=tyre_data.production_month,
            size=tyre_data.size,
            brand=tyre_data.brand,
            rubber_brand=tyre_data.rubber_brand,
            rubber_type=tyre_data.rubber_type,
            remark=tyre_data.remark,
            amount=tyre_data.amount,
            discount=tyre_data.discount,
            cgst=tyre_data.cgst,
            sgst=tyre_data.sgst,
            igst=tyre_data.igst,
            discount_amt=tyre_data.discount_amt,
            total_gst=tyre_data.total_gst,
            total_amt=tyre_data.total_amt,
            grn_no=grn_no,
            status="Off Vehicle",
        )
        db.add(tyre)

        total_amount += tyre.total_amt
        total_gst += tyre.total_gst or 0.0
        total_discount += tyre.discount_amt or 0.0

    # Update totals in GRN
    db_grn.total_tyre_count = total_tyre_count
    db_grn.total_gst = round(total_gst, 2)
    db_grn.total_discount = round(total_discount, 2)
    db_grn.total_amount = round(total_amount, 2)
    db_grn.total = round(total_amount, 2)

    db.commit()
    db.refresh(db_grn)

    return NewGRNResponse(
        grn_no=grn_no,
        grn_date=grn_date,
        org_id=data.org_id,
        zone_id=data.zone_id,
        office_id=data.office_id,
        vendor_id=data.vendor_id,
        challan_no=data.challan_no,
        total_tyre_count=total_tyre_count,
        total_gst=db_grn.total_gst,
        total_discount=db_grn.total_discount,
        total_amount=db_grn.total_amount,
        type=data.type,
        message="GRN created successfully with all tyres"
    )


@router.get("/{grn_no}", response_model=NewGRNResponse)
def get_grn_details(
    grn_no: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Fetch GRN by grn_no and return full data including org_id and zone_id.
    Access control will be handled in the frontend (same as Sensors).
    """
    grn = db.query(NewGRN).filter(NewGRN.grn_no == grn_no).first()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # Return full GRN data without strict access filtering
    return NewGRNResponse(
        grn_no=grn.grn_no,
        grn_date=grn.grn_date,
        org_id=grn.org_id,
        zone_id=grn.zone_id,
        office_id=grn.office_id,
        vendor_id=grn.vendor_id,
        challan_no=grn.challan_no,
        total_tyre_count=grn.total_tyre_count,
        total_gst=grn.total_gst,
        total_discount=grn.total_discount,
        total_amount=grn.total_amount,
        type=grn.type,
        message="GRN details retrieved successfully"
    )