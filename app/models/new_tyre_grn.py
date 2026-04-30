from sqlalchemy import UUID, Column, Integer, String, Date, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import date
from uuid import UUID as PythonUUID
from enum import Enum

from app.db.database import Base

class GRNType(str, Enum):
    NEW = "New"
    NEW_REMOULD = "New-Remould"
    CHASSIS = "Chassis"


class NewGRN(Base):
    __tablename__ = "new_grn"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grn_no = Column(String(50), unique=True, nullable=False, index=True)          
    grn_date = Column(Date, nullable=False, server_default=func.current_date())

    zone_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Foreign keys from existing tables
    office_id = Column(String, ForeignKey("offices.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("fleet_vendors.id"), nullable=False)
    
    vendor_office = Column(String(100), nullable=False)
    state = Column(String(50))
    gst_no = Column(String(20))
    
    challan_no = Column(String(50), nullable=False)
    challan_date = Column(Date, nullable=False)
    remark = Column(String(500))
    
    # Totals (calculated automatically in API)
    total = Column(Float, nullable=True)                  # subtotal before GST/discount if needed
    total_tyre_count = Column(Integer, nullable=False, default=0)
    total_gst = Column(Float, nullable=False, default=0.0)
    total_discount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    type = Column(SQLEnum(GRNType), nullable=False)
    
    # Relationship to tyres (one-to-many)
    tyres = relationship("Tyre", back_populates="grn", cascade="all, delete-orphan")


class Tyre(Base):
    __tablename__ = "tyres"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tyre_no = Column(String(50), unique=True, nullable=False, index=True)  

    zone_id = Column(UUID(as_uuid=True), nullable=True, index=True) 
    
    production_month = Column(String(10))   # e.g. "2026-03"
    size = Column(String(50), nullable=False)
    brand = Column(String(50), nullable=False)
    rubber_brand = Column(String(50))
    rubber_type = Column(String(50))
    remark = Column(String(500))
    
    amount = Column(Float, nullable=False)          
    discount = Column(Float, default=0.0)           
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    discount_amt = Column(Float, default=0.0)
    total_gst = Column(Float, default=0.0)
    total_amt = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="Off Vehicle")

    current_status = Column(String(150), nullable=False, default="In Stock")  
    
    # Link to GRN (we store grn_no so any tyre query instantly shows its GRN)
    grn_no = Column(String(50), ForeignKey("new_grn.grn_no"), nullable=False)
    
    # Relationship
    grn = relationship("NewGRN", back_populates="tyres")