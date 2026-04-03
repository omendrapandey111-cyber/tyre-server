from pydantic import BaseModel

class PlaceCreate(BaseModel):
    name: str
    short_name: str | None = None

    # ✅ FIX
    controlling_office_name: str | None = None


class OfficeMini(BaseModel):
    name: str

    class Config:
        from_attributes = True


class PlaceOut(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    controlling_office_name: str | None = None

    # ✅ nested office
    controlling_office: OfficeMini | None = None

    class Config:
        from_attributes = True