from pydantic import BaseModel

class TyreBrandOut(BaseModel):
    id: int
    brand_name: str
    manufacturer_name: str | None = None
    tyre_size: str | None = None
    tyre_construction: str | None = None
    tyre_nature: str | None = None
    ply_rating: str | None = None
    max_nsd: float | None = None
    min_nsd: float | None = None
    is_rubber: bool | None = None

    class Config:
        from_attributes = True  