from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.db.deps import get_db   # your DB session dependency
from app.models.new_tyre_grn import NewGRN, Tyre
from app.schemas.new_tyre_grn import NewGRNCreate, NewGRNResponse

router = APIRouter(prefix="/new-tyre-grn", tags=["New Tyre GRN"])


def generate_grn_no(db: Session, grn_type: str) -> str:
    #map the type to prefix
    prefix_map = {
        "New": "NW",
        "New-Remould": "NR",
        "Chassis": "CS"
    }
    prefix_code= prefix_map.get(grn_type.value)
    if not prefix_code:
        raise ValueError("Invalid GRN type")
    
    #DDMMYY format
    today = date.today().strftime("%d%m%y")
    
    # Get the highest sequence for same prefix
    last_grn = (
        db.query(NewGRN.grn_no)\
        .filter(NewGRN.grn_no.like(f"{today}%"))\
        .order_by(NewGRN.grn_no.desc())\
        .first()
    )
    if last_grn:
        seq = int(last_grn[0].split("-")[-1]) + 1
    else:
        seq = 1
    
    return f"{prefix_code}-{today}-{seq:06d}"


@router.post("/", response_model=NewGRNResponse, status_code=status.HTTP_201_CREATED)
def create_new_tyre_grn(
    data: NewGRNCreate,
    db: Session = Depends(get_db)
):
    # 1. Generate GRN number
    grn_no = generate_grn_no(db, data.type)
    
    # 2. Set default date
    grn_date = data.grn_date or date.today()
    
    # 3. Create header (totals will be overwritten by calculation)
    db_grn = NewGRN(
        grn_no=grn_no,
        grn_date=grn_date,
        office_id=data.office_id,
        vendor_id=data.vendor_id,
        vendor_office=data.vendor_office,
        state=data.state,
        gst_no=data.gst_no,
        challan_no=data.challan_no,
        challan_date=data.challan_date,
        remark=data.remark,
        type=data.type.value,
        # totals will be set after tyre loop
    )
    db.add(db_grn)
    db.commit()
    db.refresh(db_grn)
    
    # 4. Process tyres + calculate totals
    total_tyre_count = len(data.tyres)
    total_amount = 0.0
    total_gst = 0.0
    total_discount = 0.0
    grand_total = 0.0   # if you want a separate "Total" field
    
    for tyre_data in data.tyres:
        tyre = Tyre(
            tyre_no=tyre_data.tyre_no,
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
        grand_total += tyre.total_amt   # or use amount - discount + gst as you prefer
    
    # 5. Update header with calculated totals (overrides any user-sent values)
    db_grn.total_tyre_count = total_tyre_count
    db_grn.total_gst = round(total_gst, 2)
    db_grn.total_discount = round(total_discount, 2)
    db_grn.total_amount = round(total_amount, 2)
    db_grn.total = round(grand_total, 2)   # "Total" field - adjust logic if you need different subtotal
    
    db.commit()
    db.refresh(db_grn)
    
    return NewGRNResponse(
        grn_no=grn_no,
        grn_date=grn_date,
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
def get_grn_details(grn_no: str, db: Session = Depends(get_db)):
    grn = db.query(NewGRN).filter(NewGRN.grn_no == grn_no).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    return NewGRNResponse(
        grn_no=grn.grn_no,
        grn_date=grn.grn_date,
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