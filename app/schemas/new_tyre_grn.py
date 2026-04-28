from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date
from enum import Enum as PyEnum
from uuid import UUID

class GRNType(str, PyEnum):
    NEW = "New"
    NEW_REMOULD = "New-Remould"
    CHASSIS = "Chassis"


class TyreCreate(BaseModel):
    tyre_no: str = Field(..., min_length=1, description="Tyre serial number (compulsory)")
    production_month: Optional[str] = Field(None, description="e.g. 2026-03")
    size: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    rubber_brand: Optional[str] = None
    rubber_type: Optional[str] = None
    remark: Optional[str] = None
    
    amount: float = Field(..., gt=0)
    discount: Optional[float] = Field(0.0, ge=0)
    cgst: Optional[float] = Field(0.0, ge=0)
    sgst: Optional[float] = Field(0.0, ge=0)
    igst: Optional[float] = Field(0.0, ge=0)
    discount_amt: Optional[float] = Field(0.0, ge=0)
    total_gst: Optional[float] = Field(0.0, ge=0)
    total_amt: float = Field(..., gt=0)


class NewGRNCreate(BaseModel):
    # grn_no and grn_date are auto-generated in backend
    grn_date: Optional[date] = None

    org_id: UUID = Field(..., description="Organization UUID")
    zone_id: UUID = Field(..., description="Zone UUID")
    
    office_id: str = Field(..., min_length=1)
    vendor_id: str = Field(..., min_length=1)
    vendor_office: str = Field(..., min_length=1)
    state: Optional[str] = None
    gst_no: Optional[str] = None
    
    challan_no: str = Field(..., min_length=1)
    challan_date: date = Field(...)
    remark: Optional[str] = None
    
    # Totals are OPTIONAL in request - backend will calculate & override for consistency
    total: Optional[float] = None
    total_tyre_count: Optional[int] = None
    total_gst: Optional[float] = None
    total_discount: Optional[float] = None
    total_amount: Optional[float] = None
    
    type: GRNType = Field(...)
    
    tyres: List[TyreCreate] = Field(..., min_length=1, description="At least one tyre must be added")


class NewGRNResponse(BaseModel):
    grn_no: str
    grn_date: date
    zone_id: Optional[UUID] = None
    office_id: str
    vendor_id: str
    challan_no: str
    total_tyre_count: int
    total_gst: float
    total_discount: float
    total_amount: float
    type: GRNType
    message: str = "GRN created successfully"

    class Config:
        from_attributes = True
        extra = "ignore"


# Optional: validator to ensure tyre totals are consistent (optional)
    # @field_validator("tyres")
    # @classmethod
    # def validate_tyres(cls, v):
    #     for tyre in v:
    #         calculated_total_gst = (tyre.cgst or 0) + (tyre.sgst or 0) + (tyre.igst or 0)
    #         if abs((tyre.total_gst or 0) - calculated_total_gst) > 0.01:
    #             raise ValueError(f"Total GST mismatch for tyre {tyre.tyre_no}")
    #     return v