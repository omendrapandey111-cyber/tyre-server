from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturer"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)