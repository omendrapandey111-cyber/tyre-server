from app.db.database import Base, engine
from app.api import new_tyre_grn, office, place, fleet_vendor, tyre_support_master, tyres, vehicle_model, vehicle_type, transaction

from fastapi.middleware.cors import CORSMiddleware
 
Base.metadata.create_all(bind=engine)

from fastapi import FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tyre_support_master.router)

app.include_router(office.router)
app.include_router(place.router)
app.include_router(fleet_vendor.router)
app.include_router(vehicle_model.router)
app.include_router(tyres.router)
app.include_router(new_tyre_grn.router)
app.include_router(vehicle_type.router)

app.include_router(transaction.router)

@app.get("/")
def read_root():
    return {"message": "API is running"}