from fastapi import APIRouter
from . import issue_receipt, transaction, newGrn, lifecycle


router = APIRouter(prefix="/reports", tags=["Reports"])

router.include_router(issue_receipt.router)
router.include_router(transaction.router)
router.include_router(newGrn.router)
router.include_router(lifecycle.router)
