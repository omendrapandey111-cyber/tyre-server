from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from app.db.database import Base


class TyreLayout(Base):
    __tablename__ = "tyre_layouts"

    id = Column(String(20), primary_key=True, index=True)  
    layout = Column(JSONB, nullable=False)