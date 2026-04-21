from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class TyrePosition(Base):
    __tablename__ = "tyre_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    vehicle_no = Column(String(50), nullable=False, index=True)
    layout_id = Column(String(20), nullable=False)

    tyre_no = Column(String(100), nullable=True)  
    # NULL = position empty (after receipt / removal)

    position = Column(String(20), nullable=False)  
    # e.g. F1LI, R2RO

    event_type = Column(String(20), nullable=False)
    # ISSUE / RECEIPT / REPLACE_REMOVE

    reference_ir_id = Column(Integer, ForeignKey("issue_receipt.id"))

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())