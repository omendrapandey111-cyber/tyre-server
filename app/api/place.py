from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.deps import get_db_tyre as get_db
from app.models.office import Office
from app.models.place import Place
from app.schemas.place import PlaceCreate, PlaceOut

router = APIRouter(prefix="/places", tags=["Places"])


@router.post("/", response_model=PlaceOut)
def create_place(place: PlaceCreate, db: Session = Depends(get_db)):

    data = place.dict()

    # ✅ handle empty office
    if not data.get("controlling_office_name"):
        data["controlling_office_name"] = None
    else:
        office = db.query(Office).filter(
            Office.name == data["controlling_office_name"]
        ).first()
        if not office:
            raise HTTPException(400, "Invalid office")

    new_place = Place(**data)

    db.add(new_place)
    db.commit()
    db.refresh(new_place)

    return new_place


@router.get("/", response_model=list[PlaceOut])
def get_places(db: Session = Depends(get_db)):
    return (
        db.query(Place)
        .options(joinedload(Place.controlling_office))
        .all()
    )


# ✅ EDIT PLACE
@router.put("/{place_id}", response_model=PlaceOut)
def update_place(
    place_id: int,
    place: PlaceCreate,
    db: Session = Depends(get_db)
):
    db_place = db.query(Place).filter(Place.id == place_id).first()

    if not db_place:
        raise HTTPException(404, "Place not found")

    data = place.dict()

    if not data.get("controlling_office_name"):
        data["controlling_office_name"] = None
    else:
        office = db.query(Office).filter(
            Office.name == data["controlling_office_name"]
        ).first()
        if not office:
            raise HTTPException(400, "Invalid office")

    for key, value in data.items():
        setattr(db_place, key, value)

    db.commit()
    db.refresh(db_place)

    return db_place