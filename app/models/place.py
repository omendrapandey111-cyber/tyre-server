from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # 🔥 must be unique
    short_name = Column(String)

    # controlling office by NAME
    controlling_office_name = Column(String, ForeignKey("offices.name"))

    # relationships
    controlling_office = relationship(
        "Office",
        foreign_keys=[controlling_office_name]
    )

    offices = relationship(
        "Office",
        back_populates="place",
        foreign_keys="Office.place_name"
    )