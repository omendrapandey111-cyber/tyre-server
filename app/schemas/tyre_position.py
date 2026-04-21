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


class TyrePositionResponse(TyrePositionBase):
    id: int
    vehicle_no: str
    tyre_no: str
    position: str
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True