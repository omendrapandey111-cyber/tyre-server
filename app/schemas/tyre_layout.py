from pydantic import BaseModel
from typing import Dict, Any


class TyreLayoutBase(BaseModel):
    id: str
    layout: Dict[str, Any]


class TyreLayoutCreate(TyreLayoutBase):
    pass


class TyreLayoutResponse(TyreLayoutBase):
    class Config:
        from_attributes = True