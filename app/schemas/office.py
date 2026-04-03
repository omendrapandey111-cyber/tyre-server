from pydantic import BaseModel

class OfficeCreate(BaseModel):
    name: str
    city: str
    state: str
    gstin: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    place_name: str | None = None

class PlaceMini(BaseModel):
    name: str

    class Config:
        from_attributes = True

class OfficeOut(BaseModel):
    id: str
    name: str
    city: str
    state: str
    gstin: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    place_name: str | None = None

    # ✅ nested place
    place: PlaceMini | None = None

    class Config:
        from_attributes = True