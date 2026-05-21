from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class TyreLifecycleEvent(BaseModel):
    date: date
    event_type: str
    reference_no: str
    action: str
    vehicle_no: Optional[str] = None
    wheel_position: Optional[str] = None
    grn_type: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    removal_reason: Optional[str] = None
    nsd: Optional[float] = None
    km_run: Optional[float] = None
    average_nsd: Optional[float] = None
    outer_nsd: Optional[float] = None
    created_by: Optional[str] = None
    created_at: datetime


class TyreLifecycleResponse(BaseModel):
    tyre_no: str
    brand: Optional[str] = None
    size: Optional[str] = None
    total_events: int
    events: List[TyreLifecycleEvent]