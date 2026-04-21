# app/schemas/issue_receipt.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum as PyEnum


class ActionType(str, PyEnum):
    ISSUE = "Issue"
    RECEIPT = "Receipt"


class IssueReceiptDetailCreate(BaseModel):
    tyre_no: str

    # Issue
    wheel_position: Optional[str] = None

    # Receipt
    convert_to_stepney: bool = False
    outer_nsd: Optional[float] = None
    center_nsd: Optional[float] = None
    center2_nsd: Optional[float] = None
    inner_nsd: Optional[float] = None
    average_nsd: Optional[float] = None

    issue_to_stepney: bool = False
    remarks: Optional[str] = None


class IssueReceiptCreate(BaseModel):
    action_type: ActionType
    layout_id: str   

    ir_date: Optional[date] = None
    office_id: str
    vehicle_no: str
    vehicle_km: Optional[int]

    details: List[IssueReceiptDetailCreate]   

    created_by: str


class IssueReceiptResponse(BaseModel):
    id: int
    ir_no: str
    action_type: ActionType
    ir_date: date
    vehicle_no: str
    tyre_no: str
    wheel_position: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True