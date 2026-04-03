from sqlalchemy import Column, Integer, String
from app.db.database import Base

class VehicleModel(Base):
    __tablename__ = "vehicle_models"

    id = Column(Integer, primary_key=True)
    model_name = Column(String, nullable=False)

    manufacturer = Column(String)
    wheel_layout = Column(String)

    no_of_tyres = Column(Integer)
    no_of_stepney = Column(Integer)