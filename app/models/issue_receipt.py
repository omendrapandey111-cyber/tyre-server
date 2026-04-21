from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.database import Base


class IssueReceipt(Base):
    __tablename__ = "issue_receipt"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    ir_no = Column(String(30), unique=True, nullable=False, index=True)
    action_type = Column(String(10), nullable=False)   # "Issue" or "Receipt"

    ir_date = Column(Date, nullable=False, server_default=func.current_date())

    office_id = Column(String, ForeignKey("offices.id"), nullable=False)
    vehicle_no = Column(String(50), nullable=False)
    vehicle_km = Column(Integer, nullable=True)

    tyre_no = Column(String(100), nullable=False, index=True)

    # Receipt fields
    convert_to_stepney = Column(Boolean, default=False)
    outer_nsd = Column(Float)
    center_nsd = Column(Float)
    center2_nsd = Column(Float)
    inner_nsd = Column(Float)
    average_nsd = Column(Float)

    # Issue fields
    issue_to_stepney = Column(Boolean, default=False)
    wheel_position = Column(String(50))
    remarks = Column(Text)

    # Final status after this transaction
    status = Column(String(20), nullable=False)   # "On Vehicle" or "Off Vehicle"

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    office = relationship("Office", foreign_keys=[office_id])