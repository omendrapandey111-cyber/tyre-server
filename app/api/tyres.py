from urllib import response

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.new_tyre_grn import Tyre
from uuid import UUID
from app.core.security import CurrentUser, get_current_user   

router = APIRouter(prefix="/tyres", tags=["Tyres"])


@router.get("/")
def get_all_tyres(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    query = db.query(Tyre)


    tyres = db.query(Tyre).all()

    response = [
        {
            "tyre_no": t.tyre_no,
            "type": t.grn.type if t.grn else None, 
            "status": t.status,
            "grn_no": t.grn_no,
            "production_month": t.production_month,
            "size": t.size,
            "rubber_brand": t.rubber_brand,
            "rubber_type": t.rubber_type,
            "org_id": t.org_id,
            "zone_id": t.zone_id,
            "created_at": str(t.grn.grn_date) if t.grn else None
        }
        for t in tyres
    ]

    return {
        "message": "List of all tyres",
        "tyres": response
    }