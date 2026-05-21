import os
import uuid
import boto3

from fastapi import UploadFile
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

s3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto"
)


async def upload_file_to_r2(
    file: UploadFile,
    vendor_id: str,
    document_name: str
) -> str:

    allowed_extensions = ["jpg", "jpeg", "png", "pdf"]

    ext = file.filename.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise Exception("Invalid file type")

    # Optional size limit (5MB)
    file_content = await file.read()

    MAX_FILE_SIZE = 5 * 1024 * 1024

    if len(file_content) > MAX_FILE_SIZE:
        raise Exception("File too large")

    # Example:
    # ven-abc123/company_registration.pdf
    filename = f"{vendor_id}/{document_name}.{ext}"

    s3.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=filename,
        Body=file_content,
        ContentType=file.content_type
    )

    return f"{R2_PUBLIC_URL}/{filename}"