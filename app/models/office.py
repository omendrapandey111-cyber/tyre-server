from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid

def generate_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"

class Office(Base):
    __tablename__ = "offices"

    id = Column(String, primary_key=True, index=True, default=lambda: generate_uuid("off"))
    name = Column(String, unique=True, nullable=False)  # 🔥 must be unique

    city = Column(String)
    state = Column(String)
    gstin = Column(String, unique=True)

    address_line1 = Column(String)
    address_line2 = Column(String)

    # 🔥 FK by NAME
    place_name = Column(String, ForeignKey("places.name"), nullable=True)

    # relationship
    place = relationship(
        "Place",
        back_populates="offices",
        foreign_keys=[place_name]
    )