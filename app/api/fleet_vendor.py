from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.fleet_vendor import FleetVendor, generate_uuid
from app.schemas.fleet_vendor import FleetVendorOut
from app.utils.r2_upload import upload_file_to_r2

router = APIRouter(prefix="/vendors", tags=["Fleet Vendors"])


@router.post("/", response_model=FleetVendorOut)
async def create_vendor(

    name: str = Form(...),
    code: str = Form(...),

    legal_entity_name: str = Form(None),
    roles: str = Form(None),
    account_group: str = Form(None),

    office_name: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    address_line1: str = Form(None),
    address_line2: str = Form(None),

    contact_full_name: str = Form(None),
    contact_phone: str = Form(None),
    contact_email: str = Form(None),
    id_card: str = Form(None),

    account_holder_name: str = Form(None),
    bank_name: str = Form(None),
    account_number: str = Form(None),
    ifsc_code: str = Form(None),

    gst_number: str = Form(None),
    account_type: str = Form(None),

    cgst: float = Form(0.0),
    sgst: float = Form(0.0),
    igst: float = Form(0.0),

    notes: str = Form(None),

    company_registration_doc: UploadFile = File(None),
    gst_certificate_doc: UploadFile = File(None),
    bank_verification_doc: UploadFile = File(None),
    compliance_doc: UploadFile = File(None),
    address_proof_doc: UploadFile = File(None),

    db: Session = Depends(get_db)

):

    # Generate vendor ID FIRST
    vendor_id = generate_uuid("ven")

    # Upload files
    company_registration_url = (
        await upload_file_to_r2(
            company_registration_doc,
            vendor_id,
            "company_registration"
        )
        if company_registration_doc else None
    )

    gst_certificate_url = (
        await upload_file_to_r2(
            gst_certificate_doc,
            vendor_id,
            "gst_certificate"
        )
        if gst_certificate_doc else None
    )

    bank_verification_url = (
        await upload_file_to_r2(
            bank_verification_doc,
            vendor_id,
            "bank_verification"
        )
        if bank_verification_doc else None
    )

    compliance_doc_url = (
        await upload_file_to_r2(
            compliance_doc,
            vendor_id,
            "compliance"
        )
        if compliance_doc else None
    )

    address_proof_url = (
        await upload_file_to_r2(
            address_proof_doc,
            vendor_id,
            "address_proof"
        )
        if address_proof_doc else None
    )

    vendor = FleetVendor(
        id=vendor_id,
        name=name,
        code=code,

        legal_entity_name=legal_entity_name,
        roles=roles,
        account_group=account_group,

        office_name=office_name,
        city=city,
        state=state,
        address_line1=address_line1,
        address_line2=address_line2,

        contact_full_name=contact_full_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        id_card=id_card,

        account_holder_name=account_holder_name,
        bank_name=bank_name,
        account_number=account_number,
        ifsc_code=ifsc_code,

        gst_number=gst_number,
        account_type=account_type,

        cgst=cgst,
        sgst=sgst,
        igst=igst,

        notes=notes,

        company_registration_doc=company_registration_url,
        gst_certificate_doc=gst_certificate_url,
        bank_verification_doc=bank_verification_url,
        compliance_doc=compliance_doc_url,
        address_proof_doc=address_proof_url
    )

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return vendor

@router.get("/", response_model=list[FleetVendorOut])
def get_all_vendors(
    db: Session = Depends(get_db)
):

    vendors = db.query(FleetVendor).all()

    return vendors