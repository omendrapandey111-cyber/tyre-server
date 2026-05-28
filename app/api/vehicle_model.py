from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db_tyre as get_db
from app.models.vehicle_model import VehicleModel
from app.schemas.vehicle_model import VehicleModelCreate, VehicleModelOut

router = APIRouter(prefix="/vehicle-models", tags=["Vehicle Models"])


@router.post("/", response_model=VehicleModelOut)
def create_vehicle_model(data: VehicleModelCreate, db: Session = Depends(get_db)):
    vehicle_model = VehicleModel(**data.dict())

    db.add(vehicle_model)
    db.commit()
    db.refresh(vehicle_model)

    return vehicle_model


@router.get("/", response_model=list[VehicleModelOut])
def get_vehicle_models(db: Session = Depends(get_db)):
    return db.query(VehicleModel).all()