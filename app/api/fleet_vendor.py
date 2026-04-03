from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.fleet_vendor import FleetVendor
from app.schemas.fleet_vendor import FleetVendorCreate, FleetVendorOut

router = APIRouter(prefix="/vendors", tags=["Fleet Vendors"])


@router.post("/", response_model=FleetVendorOut)
def create_vendor(data: FleetVendorCreate, db: Session = Depends(get_db)):
    vendor = FleetVendor(**data.dict())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/", response_model=list[FleetVendorOut])
def get_vendors(db: Session = Depends(get_db)):
    return db.query(FleetVendor).all()
