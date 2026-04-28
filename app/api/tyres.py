from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.new_tyre_grn import Tyre
from uuid import UUID
from app.core.security import get_current_user   

router = APIRouter(prefix="/tyres", tags=["Tyres"])


@router.get("/")
def get_all_tyres(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    query = db.query(Tyre)

    if getattr(current_user, 'role', None) != 'superadmin':
        pass
    elif getattr(current_user, 'zone_id', None):
        query = query.filter(Tyre.zone_id == current_user.zone_id)
    else:
        query = query.filter(Tyre.org_id == current_user.org_id)

    tyres = query.all()

    return [
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