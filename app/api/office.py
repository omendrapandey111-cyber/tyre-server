from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.office import Office
from app.models.place import Place
from app.schemas.office import OfficeCreate, OfficeOut

router = APIRouter(prefix="/offices", tags=["Offices"])


@router.post("/", response_model=OfficeOut)
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):

    data = office.dict()

    # ✅ handle empty place
    if not data.get("place_name"):
        data["place_name"] = None
    else:
        place = db.query(Place).filter(
            Place.name == data["place_name"]
        ).first()
        if not place:
            raise HTTPException(400, "Invalid place")

    new_office = Office(**data)

    db.add(new_office)
    db.commit()
    db.refresh(new_office)

    return new_office


@router.get("/", response_model=list[OfficeOut])
def get_offices(db: Session = Depends(get_db)):
    return db.query(Office).all()


# ✅ EDIT OFFICE
@router.put("/{office_id}", response_model=OfficeOut)
def update_office(
    office_id: str,
    office: OfficeCreate,
    db: Session = Depends(get_db)
):
    db_office = db.query(Office).filter(Office.id == office_id).first()

    if not db_office:
        raise HTTPException(404, "Office not found")

    data = office.dict()

    if not data.get("place_name"):
        data["place_name"] = None
    else:
        place = db.query(Place).filter(
            Place.name == data["place_name"]
        ).first()
        if not place:
            raise HTTPException(400, "Invalid place")

    for key, value in data.items():
        setattr(db_office, key, value)

    db.commit()
    db.refresh(db_office)

    return db_office