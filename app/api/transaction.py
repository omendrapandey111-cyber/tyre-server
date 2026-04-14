from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from app.db.deps import get_db
from app.models.transaction import Transaction, TransactionDetail
from app.models.office import Office
from app.models.fleet_vendor import FleetVendor
from app.schemas.transaction import (
    GRNType,
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    TransactionDetailResponse,
    OfficeInfo,
    TyreHistoryResponse,
    VendorInfo,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ------------------------------------------------------------------ #
#  GRN NUMBER GENERATOR (auto SR-140425-000001, SC-140425-000001 etc.)
# ------------------------------------------------------------------ #
GRN_PREFIX_MAP = {
    GRNType.SEND_REMOULD:    "SR",
    GRNType.SEND_CLAIM:      "SC",
    GRNType.SCRAP:           "SP",
    GRNType.RESELL:          "RS",
    GRNType.THEFT:           "TH",
    GRNType.RECEIVE_REMOULD: "RR",
    GRNType.RECEIVE_CLAIM:   "RC",
}


def generate_grn_no(db: Session, grn_type: GRNType, txn_date: date) -> str:
    prefix = GRN_PREFIX_MAP[grn_type]
    date_str = txn_date.strftime("%d%m%y")

    last_grn = (
        db.query(Transaction.grn_no)
        .filter(Transaction.grn_no.like(f"{prefix}-{date_str}-%"))
        .order_by(Transaction.grn_no.desc())
        .first()
    )

    seq = int(last_grn[0].split("-")[-1]) + 1 if last_grn else 1
    return f"{prefix}-{date_str}-{seq:06d}"


# ------------------------------------------------------------------ #
#  HELPER: build response
# ------------------------------------------------------------------ #
def _build_response(txn: Transaction, message: str = "Success") -> TransactionResponse:
    return TransactionResponse(
        transaction_id=txn.transaction_id,
        grn_no=txn.grn_no,
        grn_type=txn.grn_type,
        transaction_date=txn.date,
        office_id=txn.office_id,
        vendor_id=txn.vendor_id,
        office=OfficeInfo.model_validate(txn.office) if txn.office else None,
        vendor=VendorInfo.model_validate(txn.vendor) if txn.vendor else None,
        total_tyres=txn.total_tyres,
        total_amount=txn.total_amount,
        remark_reason=txn.remark_reason,
        place=txn.place,
        created_by=txn.created_by,
        created_at=txn.created_at,
        details=[
            TransactionDetailResponse(
                id=d.id,
                grn_no=d.grn_no,
                tyre_no=d.tyre_no,
                vehicle_no=d.vehicle_no,
                reason=d.reason,
                nsd=d.nsd,
                km_run=d.km_run,
                remark=d.remark,
                created_at=d.created_at,
            )
            for d in txn.details
        ],
        message=message,
    )


# ------------------------------------------------------------------ #
#  CREATE TRANSACTION (Send-Remould / Send-Claim / any GRN type)
# ------------------------------------------------------------------ #
@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):

    # Validate office (required for dropdown)
    office = db.query(Office).filter(Office.id == data.office_id).first()
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office with id '{data.office_id}' not found"
        )

    # Validate vendor if provided
    vendor = None
    if data.vendor_id:
        vendor = db.query(FleetVendor).filter(FleetVendor.id == data.vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id '{data.vendor_id}' not found"
            )

    # Generate GRN number
    txn_date = data.transaction_date or date.today()
    grn_no = generate_grn_no(db, data.grn_type, txn_date)

    # Create header
    db_txn = Transaction(
        grn_no=grn_no,
        grn_type=data.grn_type,
        date=txn_date,
        office_id=data.office_id,
        vendor_id=data.vendor_id,
        total_tyres=len(data.details),
        total_amount=data.total_amount or 0.0,
        remark_reason=data.remark_reason,
        place=data.place,
        created_by=data.created_by,
    )
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)

    # Add tyre details (this maintains the full lifecycle)
    for d in data.details:
        db.add(TransactionDetail(
            grn_no=grn_no,
            tyre_no=d.tyre_no,
            vehicle_no=d.vehicle_no,
            reason=d.reason,
            nsd=d.nsd,
            km_run=d.km_run,
            remark=d.remark,
        ))

    db.commit()
    db.refresh(db_txn)

    return _build_response(db_txn, "Transaction created successfully")


# ------------------------------------------------------------------ #
#  LIST TRANSACTIONS (with filters)
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[TransactionListResponse])
def list_transactions(
    grn_type: Optional[GRNType] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    office_id: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)

    if grn_type:
        query = query.filter(Transaction.grn_type == grn_type)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    if office_id:
        query = query.filter(Transaction.office_id == office_id)
    if vendor_id:
        query = query.filter(Transaction.vendor_id == vendor_id)

    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    return [
        TransactionListResponse(
            transaction_id=t.transaction_id,
            grn_no=t.grn_no,
            grn_type=t.grn_type,
            transaction_date=t.date,
            office_id=t.office_id,
            vendor_id=t.vendor_id,
            office=OfficeInfo.model_validate(t.office) if t.office else None,
            vendor=VendorInfo.model_validate(t.vendor) if t.vendor else None,
            total_tyres=t.total_tyres,
            total_amount=t.total_amount,
            created_by=t.created_by,
            created_at=t.created_at,
        )
        for t in transactions
    ]


# ------------------------------------------------------------------ #
#  TYRE LIFECYCLE - Get full history of one tyre
# ------------------------------------------------------------------ #
@router.get("/tyre/{tyre_no}", response_model=List[TyreHistoryResponse])
def get_tyre_history(tyre_no: str, db: Session = Depends(get_db)):
    # Join TransactionDetail with Transaction to get grn_type + date
    results = (
        db.query(
            TransactionDetail.id,
            TransactionDetail.grn_no,
            Transaction.grn_type,           # ← GRN Type added
            Transaction.date.label("transaction_date"),  # renamed for clarity

            TransactionDetail.tyre_no,
            TransactionDetail.vehicle_no,
            TransactionDetail.reason,
            TransactionDetail.nsd,
            TransactionDetail.km_run,
            TransactionDetail.remark,
            TransactionDetail.created_at,

            Transaction.office_id,
            Office.name.label("office_name"),      # optional but useful
            Transaction.vendor_id,
            FleetVendor.name.label("vendor_name"), # optional
        )
        .join(Transaction, Transaction.grn_no == TransactionDetail.grn_no)
        .outerjoin(Office, Office.id == Transaction.office_id)      # optional
        .outerjoin(FleetVendor, FleetVendor.id == Transaction.vendor_id)  # optional
        .filter(TransactionDetail.tyre_no == tyre_no)
        .order_by(Transaction.date.desc(), TransactionDetail.id.desc())
        .all()
    )

    if not results:
        raise HTTPException(
            status_code=404, 
            detail=f"No history found for tyre '{tyre_no}'"
        )

    # Convert raw query results (tuples) to Pydantic models
    return [
        TyreHistoryResponse(
            id=row.id,
            grn_no=row.grn_no,
            grn_type=row.grn_type,
            transaction_date=row.transaction_date,
            tyre_no=row.tyre_no,
            vehicle_no=row.vehicle_no,
            reason=row.reason,
            nsd=row.nsd,
            km_run=row.km_run,
            remark=row.remark,
            office_id=row.office_id,
            office_name=row.office_name,
            vendor_id=row.vendor_id,
            vendor_name=row.vendor_name,
            created_at=row.created_at,
        )
        for row in results
    ]


# ------------------------------------------------------------------ #
#  GET SINGLE TRANSACTION
# ------------------------------------------------------------------ #
@router.get("/{grn_no}", response_model=TransactionResponse)
def get_transaction(grn_no: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.grn_no == grn_no).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{grn_no}' not found")
    return _build_response(txn, "Transaction details retrieved successfully")