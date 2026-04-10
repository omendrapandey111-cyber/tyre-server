from pydantic import BaseModel


class ManufacturerOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True