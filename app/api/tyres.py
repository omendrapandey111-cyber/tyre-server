from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.new_tyre_grn import Tyre

router = APIRouter(prefix="/tyres", tags=["Tyres"])


@router.get("/")
def get_all_tyres(db: Session = Depends(get_db)):
    tyres = db.query(Tyre).all()

    return [
        {
            "tyre_no": t.tyre_no,
            "type": t.grn.type if t.grn else None,   # 🔥 coming from GRN
            "status": "Off Vehicle",                 # default for now
            "grn_no": t.grn_no,
            "production_month": t.production_month,
            "size": t.size,
            "rubber_brand": t.rubber_brand,
            "rubber_type": t.rubber_type,
            "created_at": str(t.grn.grn_date) if t.grn else None
        }
        for t in tyres
    ]