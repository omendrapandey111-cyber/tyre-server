from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.manufacturer import Manufacturer
from app.models.tyre_brand import TyreBrand
from app.schemas.manufacturer import ManufacturerOut
from app.schemas.tyre_brand import TyreBrandOut

router = APIRouter(prefix="/master", tags=["Master Data"])


# 🔹 Get all manufacturers
@router.get("/manufacturers", response_model=list[ManufacturerOut])
def get_manufacturers(db: Session = Depends(get_db)):
    return db.query(Manufacturer).all()


# 🔹 Get all tyre brands
@router.get("/tyre-brands", response_model=list[TyreBrandOut])
def get_tyre_brands(db: Session = Depends(get_db)):
    return db.query(TyreBrand).all()