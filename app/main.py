from app.db.database import Base, engine
from app.api import issue_receipt, new_tyre_grn, office, place, fleet_vendor, tyre_layout, tyre_position, tyre_support_master, tyres, vehicle_model, vehicle_type, transaction
from app.api.reports.router import router as reports_router
from fastapi.middleware.cors import CORSMiddleware
 
#Base.metadata.create_all(bind=engine)

from fastapi import Depends, FastAPI
app = FastAPI(title="Tyre Management API")

from app.auth.dependencies import get_current_user

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(tyre_support_master.router)

# app.include_router(office.router)
# app.include_router(place.router)
# app.include_router(fleet_vendor.router)
# app.include_router(vehicle_model.router)
# app.include_router(tyres.router)
# app.include_router(new_tyre_grn.router)
# app.include_router(vehicle_type.router)
# app.include_router(issue_receipt.router)
# app.include_router(transaction.router)


protected_routers = [
    tyre_support_master.router,
    office.router,
    place.router,
    fleet_vendor.router,
    vehicle_model.router,
    tyres.router,
    new_tyre_grn.router,
    vehicle_type.router,
    issue_receipt.router,
    transaction.router,
    tyre_layout.router,
    tyre_position.router,
    reports_router,
]

for router in protected_routers:
    app.include_router(router, dependencies=[Depends(get_current_user)])


#Public routes
@app.get("/")
def read_root():
    return {"message": "API is running"}

handler = app