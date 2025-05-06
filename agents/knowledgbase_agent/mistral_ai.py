import os
import io
import base64
import logging
from dotenv import load_dotenv
from PIL import Image
import boto3
from mistralai import Mistral, DocumentURLChunk

# Load environment variables
load_dotenv()

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Init S3 client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

logging.basicConfig(filename="mistral_conversion.log", level=logging.INFO, format="%(message)s")

def upload_to_s3(bucket, key, data_bytes):
    """Upload binary data to S3"""
    s3.upload_fileobj(io.BytesIO(data_bytes), bucket, key)
    logging.info(f"✅ Uploaded to s3://{bucket}/{key}")

def get_condition_from_filename(filename: str) -> str:
    """Extract condition name from filename like Cholestrol_1.pdf → Cholestrol"""
    return filename.split("_")[0]

def replace_image_references(md: str, images: dict, condition: str, file_prefix: str) -> str:
    """Replace image placeholders with S3 URLs after uploading"""
    for img_id, img_base64 in images.items():
        img_data = base64.b64decode(img_base64.split(",")[-1])
        image_filename = f"{file_prefix}_{img_id}.png"
        s3_key = f"Markdown_Conversions/{condition}/Images/{image_filename}"

        image = Image.open(io.BytesIO(img_data)).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        upload_to_s3(AWS_BUCKET, s3_key, buffer.read())

        image_url = f"https://{AWS_BUCKET}.s3.amazonaws.com/{s3_key}"
        md = md.replace(f"![{img_id}]({img_id})", f"![{image_filename}]({image_url})")

    return md

def mistral_pdf_to_md(pdf_bytes: bytes, file_name: str, condition: str):
    """Use Mistral OCR to convert PDF to Markdown and upload result"""
    client = Mistral(api_key=MISTRAL_API_KEY)
    pdf_bytes_io = io.BytesIO(pdf_bytes)

    try:
        print(f"🔁 Uploading {file_name}.pdf to Mistral...")
        uploaded = client.files.upload(file={"file_name": "temp.pdf", "content": pdf_bytes_io.read()}, purpose="ocr")
        signed_url = client.files.get_signed_url(file_id=uploaded.id, expiry=2)
        result = client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=True
        )
    except Exception as e:
        print(f"❌ Mistral OCR failed for {file_name}: {e}")
        return

    full_markdown = ""
    image_counter = 0

    for page in result.pages:
        images = {img.id: img.image_base64 for img in page.images}
        md_with_links = replace_image_references(page.markdown, images, condition, file_name)
        full_markdown += md_with_links + "\n\n"
        image_counter += len(images)

    md_key = f"Markdown_Conversions/{condition}/{file_name}.md"
    upload_to_s3(AWS_BUCKET, md_key, full_markdown.encode("utf-8"))

    return {
        "markdown_s3_path": md_key,
        "images_uploaded": image_counter,
        "preview_url": f"https://{AWS_BUCKET}.s3.amazonaws.com/{md_key}"
    }

def process_pdf_from_s3(file_name: str):
    """Downloads PDF from S3 and processes it"""
    s3_key = f"RAW_PDFs/{file_name}"
    file_name_no_ext = os.path.splitext(file_name)[0]
    condition = get_condition_from_filename(file_name)

    print(f"📥 Downloading {file_name} from s3://{AWS_BUCKET}/{s3_key}...")
    try:
        response = s3.get_object(Bucket=AWS_BUCKET, Key=s3_key)
        pdf_bytes = response["Body"].read()
    except Exception as e:
        print(f"❌ Failed to download {file_name} from S3:", str(e))
        return

    result = mistral_pdf_to_md(pdf_bytes, file_name_no_ext, condition)
    if result:
        print("✅ Markdown and images uploaded:")
        print(f"📝 {result['preview_url']}")
        print(f"🖼️ Images uploaded: {result['images_uploaded']}")

if __name__ == "__main__":
    # Chronic condition PDFs (your list)
    pdf_files = [
        "Cholesterol_1.pdf",
        "Cholesterol_Food.pdf",
        "CKD_1.pdf",
        "CKD_Food.pdf",
        "Gluten_Intoleraance_Food_2.pdf",
        "Gluten_Intolerance_1.pdf",
        "Gluten_Intolerance_Food_1.pdf",
        "Hypertension_1.pdf",
        "Hypertension_Food.pdf",
        "Polycystic_Overy_Syndrome.pdf",
        "Polycystic_Overy_Syndrome_Food.pdf",
        "Type2_Diabetes_1.pdf",
        "Type2_Diabetes_Food.pdf",
        "Obesity_1.pdf",
        "Obesity_Food_1.pdf"
    ]

    for pdf in pdf_files:
        print(f"\n📄 Processing: {pdf}")
        process_pdf_from_s3(pdf)
