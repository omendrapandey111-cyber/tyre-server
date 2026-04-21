from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.tyre_layouts import TyreLayout
from app.schemas.tyre_layout import (
    TyreLayoutCreate,
    TyreLayoutResponse
)

router = APIRouter(prefix="/tyre-layouts", tags=["Tyre Layouts"])

@router.get("/", response_model=list[TyreLayoutResponse])
def get_all_layouts(db: Session = Depends(get_db)):
    return db.query(TyreLayout).all()


@router.get("/{layout_id}", response_model=TyreLayoutResponse)
def get_layout(layout_id: str, db: Session = Depends(get_db)):

    layout = db.query(TyreLayout).filter(TyreLayout.id == layout_id).first()

    if not layout:
        raise HTTPException(404, "Layout not found")

    return layout