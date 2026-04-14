from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from enum import Enum

from app.db.database import Base


class GRNType(str, Enum):
    SEND_REMOULD    = "Send-Remould"
    SEND_CLAIM      = "Send-Claim"
    SCRAP           = "Scrap"
    RESELL          = "Resell"
    THEFT           = "Theft"
    RECEIVE_REMOULD = "Receive-Remould"
    RECEIVE_CLAIM   = "Receive-Claim"


class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id  = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grn_no          = Column(String(30), unique=True, nullable=False, index=True)   # auto-generated e.g. SR-140425-000001
    grn_type        = Column(SQLEnum(GRNType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    date            = Column(Date, nullable=False, server_default=func.current_date())

    # FK to existing offices table - stored as string for flexibility
    office_id = Column(String, ForeignKey("offices.id"), nullable=False)
    office    = relationship("Office", foreign_keys=[office_id])
    vendor_id = Column(String, ForeignKey("fleet_vendors.id"), nullable=True)
    vendor    = relationship("FleetVendor", foreign_keys=[vendor_id])

    total_tyres     = Column(Integer, nullable=False, default=0)
    total_amount    = Column(Float, nullable=False, default=0.0)
    remark_reason   = Column(Text, nullable=True)
    place           = Column(String(255), nullable=True)

    created_by      = Column(String(255), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # One-to-many: one transaction has many tyre detail rows
    details = relationship("TransactionDetail", back_populates="transaction", cascade="all, delete-orphan")


class TransactionDetail(Base):
    __tablename__ = "transaction_details"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grn_no      = Column(String(30), ForeignKey("transaction.grn_no"), nullable=False, index=True)
    tyre_no     = Column(String(100), nullable=False, index=True)
    vehicle_no  = Column(String(50), nullable=True)
    reason      = Column(Text, nullable=True)
    nsd         = Column(Float, nullable=True)      # Tyre tread depth in mm
    km_run      = Column(Integer, nullable=True)
    remark      = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Back-reference to parent transaction
    transaction = relationship("Transaction", back_populates="details")