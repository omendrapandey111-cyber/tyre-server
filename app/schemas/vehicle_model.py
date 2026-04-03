from pydantic import BaseModel


class VehicleModelCreate(BaseModel):
    model_name: str
    manufacturer: str
    wheel_layout: str | None = None

    no_of_tyres: int
    no_of_stepney: int


class VehicleModelOut(VehicleModelCreate):
    id: int
    model_name: str
    manufacturer: str

    class Config:
        from_attributes = True