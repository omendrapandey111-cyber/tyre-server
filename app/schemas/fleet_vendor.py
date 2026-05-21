from typing import Optional
from pydantic import BaseModel

class FleetVendorCreate(BaseModel):
    name: str
    code: str
    legal_entity_name: str | None = None
    roles: str | None = None
    account_group: str | None = None

    office_name: str | None = None
    city: str | None = None
    state: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None

    contact_full_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    id_card: str | None = None

    account_holder_name: str | None = None
    bank_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None
    gst_number: str | None = None
    account_type: str | None = None
    cgst: Optional[float] | None = 0.0
    sgst: Optional[float] | None = 0.0  
    igst: Optional[float] | None = 0.0
    notes: Optional[str] | None = None

    company_registration_doc: Optional[str] | None = None
    gst_certificate_doc: Optional[str] | None = None
    bank_verification_doc: Optional[str] | None = None
    compliance_doc: Optional[str] | None = None
    address_proof_doc: Optional[str] | None = None


class FleetVendorOut(FleetVendorCreate):
    id: str
    name: str
    office_name: str
    state: str
    gst_number: str | None
    
    class Config:
        from_attributes = True