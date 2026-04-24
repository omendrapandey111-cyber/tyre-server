from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.deps import get_db
from app.models.tyre_position import TyrePosition
from app.schemas.tyre_position import TyrePositionResponse
from app.utils.tyre import parse_position

router = APIRouter(prefix="/tyre-positions", tags=["Tyre Positions"])

#full logs history
@router.get("/", response_model=list[TyrePositionResponse])
def get_all_positions(db: Session = Depends(get_db)):
    rows = db.query(TyrePosition).order_by(TyrePosition.created_at.desc()).all()

    for r in rows:
        parsed = parse_position(r.position)
        r.name = parsed["name"]
    return rows



# Get history of a specific vehicle
@router.get("/vehicle/{vehicle_no}", response_model=list[TyrePositionResponse])
def get_vehicle_history(vehicle_no: str, db: Session = Depends(get_db)):

    data = db.query(TyrePosition)\
        .filter(TyrePosition.vehicle_no == vehicle_no)\
        .order_by(TyrePosition.created_at.desc())\
        .all()
    
    for r in data:
        parsed = parse_position(r.position)
        r.name = parsed["name"]

    return data


# Get current positions of a specific vehicle 
@router.get("/vehicle/{vehicle_no}/current")
def get_current_positions(vehicle_no: str, db: Session = Depends(get_db)):

    rows = db.query(TyrePosition)\
        .filter(TyrePosition.vehicle_no == vehicle_no)\
        .order_by(
            TyrePosition.position,
            TyrePosition.created_at.desc()
        )\
        .all()

    latest_map = {}

    for row in rows:
        if row.position not in latest_map:
            parsed =parse_position(row.position)
            row.name = parsed["name"]
            latest_map[row.position] = row

    return list(latest_map.values())



@router.get("/current-all")
def get_current_all_tyres(db: Session = Depends(get_db)):

    query = text("""
        SELECT 
            t.tyre_no,
            tp.vehicle_no,
            tp.position,
            tp.event_type,
            tp.created_at
        FROM tyres t
        LEFT JOIN (
            SELECT DISTINCT ON (tyre_no)
                tyre_no,
                vehicle_no,
                position,
                event_type,
                created_at
            FROM tyre_positions
            ORDER BY tyre_no, created_at DESC
        ) tp ON t.tyre_no = tp.tyre_no
    """)

    result = db.execute(query).fetchall()

    response = []

    for row in result:
        row = dict(row._mapping)

        # If no history exists → OFF VEHICLE
        if row["event_type"] is None:
            response.append({
                "tyre_no": row["tyre_no"],
                "vehicle_no": None,
                "position": None,
                "name": None,
                "status": "Off Vehicle",
                "last_updated": None
            })
            continue

        # If latest event is RECEIPT → OFF VEHICLE
        if row["event_type"] == "RECEIPT":
            response.append({
                "tyre_no": row["tyre_no"],
                "vehicle_no": None,
                "position": None,
                "name": None,
                "status": "Off Vehicle",
                "last_updated": row["created_at"]
            })
        else:
            name = None
            if row["position"]:
                parsed = parse_position(row["position"])
                name = parsed["name"]

            response.append({
                "tyre_no": row["tyre_no"],
                "vehicle_no": row["vehicle_no"],
                "position": row["position"],
                "name": name,
                "status": "On Vehicle",
                "last_updated": row["created_at"]
            })

    return response


# Get history of a specific tyre
@router.get("/{tyre_no}", response_model=list[TyrePositionResponse])
def get_tyre_history(tyre_no: str, db: Session = Depends(get_db)):

    rows = db.query(TyrePosition)\
        .filter(TyrePosition.tyre_no == tyre_no)\
        .order_by(TyrePosition.created_at.desc())\
        .all()

    if not rows:
        raise HTTPException(404, f"No history found for tyre {tyre_no}")

    for r in rows:
        if r.position:
            parsed = parse_position(r.position)
            r.name = parsed["name"]
        else:
            r.name = None

    return rows