from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db_tyre as get_db
from app.models.vehicle_type import VehicleType
from app.schemas.vehicle_type import VehicleTypeCreate, VehicleTypeOut

router = APIRouter(prefix="/vehicle-types", tags=["Vehicle Types"])

@router.post("/", response_model=VehicleTypeOut)
def create_vehicle_type(data: VehicleTypeCreate, db: Session = Depends(get_db)):

    #check if the vehicle type already exists
    existing = db.query(VehicleType).filter(VehicleType.name == data.name).first()
    if existing:
        return existing 
    
    vehicle_type = VehicleType(**data.dict())
    db.add(vehicle_type)
    db.commit()
    db.refresh(vehicle_type)
    return vehicle_type


@router.get("/", response_model=list[VehicleTypeOut])
def get_vehicle_types(db: Session = Depends(get_db)):
    return db.query(VehicleType).all()