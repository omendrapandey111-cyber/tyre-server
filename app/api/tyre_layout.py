from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db_tyre as get_db
from app.models.tyre_layouts import TyreLayout
from app.schemas.tyre_layout import (
    TyreLayoutResponse
)
from app.utils.tyre import parse_position

router = APIRouter(prefix="/tyre-layouts", tags=["Tyre Layouts"])

@router.get("/", response_model=list[TyreLayoutResponse])
def get_all_layouts(db: Session = Depends(get_db)):
    layouts = db.query(TyreLayout).all()

    for layout in layouts:
        if layout.layout and "tyres" in layout.layout:
            layout.layout["tyres"] = [
                {**t, **parse_position(t["position"])} 
                for t in layout.layout["tyres"]
            ]
    return layouts


@router.get("/{layout_id}", response_model=TyreLayoutResponse)
def get_layout(layout_id: str, db: Session = Depends(get_db)):

    layout = db.query(TyreLayout).filter(TyreLayout.id == layout_id).first()

    if not layout:
        raise HTTPException(404, "Layout not found")
    if layout.layout and "tyres" in layout.layout:
        layout.layout["tyres"] = [
            {**t, **parse_position(t["position"])}
            for t in layout.layout["tyres"]
        ]

    return layout