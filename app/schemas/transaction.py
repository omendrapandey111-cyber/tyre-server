from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum as PyEnum


class GRNType(str, PyEnum):
    SEND_REMOULD = "Send-Remould"
    SEND_CLAIM = "Send-Claim"
    SCRAP = "Scrap"
    RESELL = "Resell"
    THEFT = "Theft"
    RECEIVE_REMOULD = "Receive-Remould"
    RECEIVE_CLAIM = "Receive-Claim"


# REQUEST MODELS
class TransactionDetailCreate(BaseModel):
    tyre_no: str = Field(..., min_length=1, description="Tyre serial / identification number")
    vehicle_no: Optional[str] = Field(None, description="Vehicle registration number")
    reason: Optional[str] = Field(None, description="Reason for this tyre's movement")
    nsd: Optional[float] = Field(None, ge=0, description="Tyre tread depth (mm)")
    km_run: Optional[int] = Field(None, ge=0, description="Kilometres run on this tyre")
    remark: Optional[str] = Field(None)


class TransactionCreate(BaseModel):
    """Simplified request - uses office_id / vendor_id for dropdown selection"""
    grn_type: GRNType = Field(...)
    transaction_date: Optional[date] = None

    # Use IDs (frontend will send ID selected from dropdown)
    office_id: str = Field(..., min_length=1)
    vendor_id: Optional[str] = Field(None)

    remark_reason: Optional[str] = Field(None)
    place: Optional[str] = Field(None)
    created_by: str = Field(..., min_length=1)

    total_amount: Optional[float] = Field(None, ge=0)

    details: List[TransactionDetailCreate] = Field(..., min_length=1)


# SIMPLE RESPONSE HELPERS (for nested office/vendor in responses)
class OfficeInfo(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class VendorInfo(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


# RESPONSE MODELS
class TransactionDetailResponse(BaseModel):
    id: int
    grn_no: str
    tyre_no: str
    vehicle_no: Optional[str]
    reason: Optional[str]
    nsd: Optional[float]
    km_run: Optional[int]
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    transaction_id: int
    grn_no: str
    grn_type: GRNType
    transaction_date: date
    office_id: str
    vendor_id: Optional[str] = None
    office: Optional[OfficeInfo] = None
    vendor: Optional[VendorInfo] = None
    total_tyres: int
    total_amount: float
    remark_reason: Optional[str]
    place: Optional[str]
    created_by: str
    created_at: datetime
    details: List[TransactionDetailResponse] = []
    message: str = "Transaction created successfully"

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Lightweight list response"""
    transaction_id: int
    grn_no: str
    grn_type: GRNType
    transaction_date: date
    office_id: str
    vendor_id: Optional[str] = None
    office: Optional[OfficeInfo] = None
    vendor: Optional[VendorInfo] = None
    total_tyres: int
    total_amount: float
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True



class TyreHistoryResponse(BaseModel):
    """Response for tyre lifecycle - includes GRN Type and key transaction info"""
    id: int
    grn_no: str
    grn_type: GRNType          
    transaction_date: date    

    tyre_no: str
    vehicle_no: Optional[str]
    reason: Optional[str]
    nsd: Optional[float]
    km_run: Optional[int]
    remark: Optional[str]

    office_id: str
    office_name: Optional[str] = None   # Optional: for better readability
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True