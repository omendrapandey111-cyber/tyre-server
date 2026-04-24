from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TyrePositionBase(BaseModel):
    vehicle_no: str
    layout_id: str
    tyre_no: Optional[str]
    position: str
    event_type: str
    reference_ir_id: Optional[int]
    created_by: str


class TyrePositionCreate(TyrePositionBase):
    pass


class TyrePositionResponse(BaseModel):
    id: int
    tyre_no: str
    vehicle_no: str
    position: str
    name: str | None= None
    event_type: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True