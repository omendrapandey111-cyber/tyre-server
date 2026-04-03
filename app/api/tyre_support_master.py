from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.manufacturer import Manufacturer
from app.models.tyre_brand import TyreBrand

router = APIRouter(prefix="/master", tags=["Master Data"])


# 🔹 Get all manufacturers
@router.get("/manufacturers")
def get_manufacturers(db: Session = Depends(get_db)):
    return db.query(Manufacturer).all()


# 🔹 Get all tyre brands
@router.get("/tyre-brands")
def get_tyre_brands(db: Session = Depends(get_db)):
    return db.query(TyreBrand).all()