from fastapi import APIRouter, Depends, Query, HTTPException
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.deps import get_db_tyre
from app.models.new_tyre_grn import Tyre
from app.core.security import CurrentUser, get_current_user
from typing import List   

router = APIRouter(prefix="/tyres", tags=["Tyres"])

#helper function for zone filtering
def get_zone_filter(current_user: CurrentUser = Depends(get_current_user)):
    """Return zone_id if user is not admin"""
    if current_user.role == "admin" or current_user.zone_id is None:
        return None
    return current_user.zone_id

@router.get("/")
def get_all_tyres(db: Session = Depends(get_db_tyre), zone_id: UUID | None = Depends(get_zone_filter)):
    query = db.query(Tyre)
    if zone_id:
        query = query.filter(Tyre.zone_id == zone_id)
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
            "zone_id": t.zone_id,
            "current_status": t.current_status,
            "created_at": str(t.grn.grn_date) if t.grn else None
        }
        for t in tyres
    ]

@router.get("/inventory")
def get_inventory_tyres(db: Session = Depends(get_db_tyre), zone_id: UUID | None = Depends(get_zone_filter),
    statuses: List[str] = Query(
        default = ["In Stock", "Receive-Remould", "Receive-Claim", "Rotation"],
        description = "Filter tyres by their current status. Multiple statuses can be provided."
    )):
    """
    Inventory endpoint to fetch tyres based on their current status. 
    """
    allowed_statuses = ["In Stock", "Receive-Remould", "Receive-Claim", "Rotation"]

    #validate that provided statuses are valid
    for status in statuses:
        if status not in allowed_statuses:
            raise ValueError(f"Invalid status: {status}. Allowed statuses are: {allowed_statuses}")
        
    query = db.query(Tyre).filter(Tyre.current_status.in_(statuses))
    if zone_id:
        query = query.filter(Tyre.zone_id == zone_id)
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
            "zone_id": t.zone_id,
            "current_status": t.current_status,
            "created_at": str(t.grn.grn_date) if t.grn else None
        }
        for t in tyres
    ]