import boto3
import os
from dotenv import load_dotenv

# Load AWS credentials from .env
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
RAW_PDF_PREFIX = "RAW_PDFs/"  # Target folder in S3

# Path to your local PDF folder
LOCAL_PDF_DIR = "/Users/vemana/Documents/Big_Data_Final_Project/agents/knowledgbase_agent/pdfs"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def upload_pdf(file_path):
    """Uploads a single PDF to S3."""
    file_name = os.path.basename(file_path)
    s3_key = f"{RAW_PDF_PREFIX}{file_name}"

    try:
        s3_client.upload_file(file_path, BUCKET_NAME, s3_key)
        print(f"✅ Uploaded: {file_name} → s3://{BUCKET_NAME}/{s3_key}")
    except Exception as e:
        print(f"❌ Error uploading {file_name}: {e}")

def upload_all_pdfs():
    """Uploads all PDFs in the specified local directory to S3."""
    if not os.path.exists(LOCAL_PDF_DIR):
        print(f"❌ Directory not found: {LOCAL_PDF_DIR}")
        return

    for file in os.listdir(LOCAL_PDF_DIR):
        if file.lower().endswith(".pdf"):
            full_path = os.path.join(LOCAL_PDF_DIR, file)
            upload_pdf(full_path)

if __name__ == "__main__":
    upload_all_pdfs()
