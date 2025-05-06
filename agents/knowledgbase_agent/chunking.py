# FILE: agents/knowledgebase_agent/chunking.py

import os
import openai
import boto3
from pinecone import Pinecone
from dotenv import load_dotenv

# ==== Load environment variables ====
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

openai.api_key = OPENAI_API_KEY

# ==== AWS S3 Client ====
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ==== Pinecone Client ====
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# ==== Count tokens (simple fallback, not tiktoken) ====
def token_count(text: str) -> int:
    return len(text.split())


# ==== Recursive Text Splitter ====
def recursive_split(text, max_tokens=300):
    print(f"🪓 Splitting large text block...")

    if token_count(text) <= max_tokens:
        return [text]

    for splitter in ["\n\n", "\n", ". "]:
        parts = text.split(splitter)
        if len(parts) == 1:
            continue

        chunks, current = [], ""
        for part in parts:
            candidate = (current + splitter + part).strip() if current else part.strip()
            if token_count(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.extend(recursive_split(current, max_tokens))
                current = part.strip()

        if current:
            chunks.extend(recursive_split(current, max_tokens))

        return chunks

    return [text]


# ==== Load Markdown from S3 ====
def load_md_from_s3(condition: str, file_name: str) -> str:
    key = f"Markdown_Conversions/{condition}/{file_name}.md"
    try:
        print(f"📥 Downloading: {key} from S3...")
        response = s3.get_object(Bucket=AWS_BUCKET, Key=key)
        return response["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"❌ Failed to load {key} from S3:", e)
        return ""


# ==== Get OpenAI Embedding ====
def get_embedding(text: str) -> list:
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print("❌ Error embedding text:", e)
        return []


# ==== Upload to Pinecone ====
def upload_chunks_to_pinecone(chunks, condition, file_name):
    batch = []
    source_path = f"{condition}/{file_name}.md"

    print(f"🚀 Uploading chunks to Pinecone for {source_path}...")

    for idx, chunk in enumerate(chunks):
        chunk_id = f"{condition}_{file_name}_{idx}"
        embedding = get_embedding(chunk)
        if not embedding:
            print(f"⚠️ Skipped chunk {idx} due to empty embedding.")
            continue

        metadata = {
            "condition": condition,
            "source_file": source_path,
            "chunk_index": idx,
            "text": chunk
        }

        print(f"📦 Prepared chunk: {chunk_id} with metadata: {metadata}")
        batch.append((chunk_id, embedding, metadata))

        if len(batch) >= 20:
            print(f"🔼 Upserting batch of {len(batch)}...")
            index.upsert(vectors=batch)
            batch.clear()

    if batch:
        print(f"🔼 Final upsert of {len(batch)} chunks...")
        index.upsert(vectors=batch)


# ==== Full Pipeline ====
def process_file(condition: str, file_name: str):
    print(f"\n📄 Processing: {condition}/{file_name}.md")

    markdown = load_md_from_s3(condition, file_name)
    if not markdown:
        print(f"⚠️ Skipped {file_name} due to missing content.")
        return

    chunks = recursive_split(markdown)
    print(f"🧱 Total chunks created: {len(chunks)}")
    upload_chunks_to_pinecone(chunks, condition, file_name)


# ==== MAIN ====
if __name__ == "__main__":
    files_to_process = {
        "Cholesterol": ["Cholesterol_1", "Cholesterol_Food"],
        "CKD": ["CKD_1", "CKD_Food"],
        "Gluten": ["Gluten_Intolerance_1", "Gluten_Intolerance_Food_1", "Gluten_Intoleraance_Food_2"],
        "Hypertension": ["Hypertension_1", "Hypertension_Food"],
        "Polycystic": ["Polycystic_Overy_Syndrome", "Polycystic_Overy_Syndrome_Food"],
        "Type2": ["Type2_Diabetes_1", "Type2_Diabetes_Food"],
        "Obesity": ["Obesity_1", "Obesity_Food_1"]
    }

    for condition, file_list in files_to_process.items():
        for file in file_list:
            process_file(condition, file)