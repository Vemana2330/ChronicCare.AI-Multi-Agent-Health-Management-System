import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read connection parameters
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT", "5432")  # default port
dbname = os.getenv("POSTGRES_DB")          # your existing DB name
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")

# Attempt connection
try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="require"
    )
    print("✅ Successfully connected to PostgreSQL!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
