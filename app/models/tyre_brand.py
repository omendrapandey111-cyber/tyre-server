from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.db.database import Base


class TyreBrand(Base):
    __tablename__ = "tyre_brands"

    id = Column(Integer, primary_key=True)

    brand_name = Column(String, nullable=False)

    manufacturer_name = Column(String, ForeignKey("manufacturer.name"))

    tyre_size = Column(String)
    tyre_construction = Column(String)
    tyre_nature = Column(String)

    ply_rating = Column(String)

    max_nsd = Column(Float)
    min_nsd = Column(Float)

    is_rubber = Column(Boolean, default=False)