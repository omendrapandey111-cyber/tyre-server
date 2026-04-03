import uuid

from sqlalchemy import Column, Integer, String, Text
from app.db.database import Base

def generate_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class FleetVendor(Base):
    __tablename__ = "fleet_vendors"

    id = Column(String, primary_key=True, index=True, default=generate_uuid("ven"))

    # 🔹 Basic Info
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    legal_entity_name = Column(String)

    roles = Column(String)              # can store comma-separated roles
    account_group = Column(String)

    # 🔹 Office Details
    office_name = Column(String)
    city = Column(String)
    state = Column(String)

    address_line1 = Column(String)
    address_line2 = Column(String)

    # 🔹 Contact Person
    contact_full_name = Column(String)
    contact_phone = Column(String)
    contact_email = Column(String)

    id_card = Column(String)   # file path or unique ID reference

    # 🔹 Bank Details
    account_holder_name = Column(String)
    bank_name = Column(String)
    account_number = Column(String)
    ifsc_code = Column(String)

    gst_number = Column(String)
    account_type = Column(String)

    # 🔹 Documents (store file paths or URLs)
    company_registration_doc = Column(String, nullable=True)
    gst_certificate_doc = Column(String, nullable=True)
    bank_verification_doc = Column(String, nullable=True)
    compliance_doc = Column(String, nullable=True)
    address_proof_doc = Column(String, nullable=True)

    # 🔹 Optional metadata
    notes = Column(Text)