# FILE: agents/nutrition_agent/snowflake_connector.py

import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ========== Load Environment Variables ==========
load_dotenv()
logging.debug("🔐 Loaded environment variables from .env")

# ========== Extract Snowflake Config ==========
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")

logging.debug(f"📦 Snowflake Config → USER={SNOWFLAKE_USER}, ACCOUNT={SNOWFLAKE_ACCOUNT}, DB={SNOWFLAKE_DATABASE}, SCHEMA={SNOWFLAKE_SCHEMA}, WH={SNOWFLAKE_WAREHOUSE}")

# ========== Build Connection String ==========
connection_string = f"snowflake://{SNOWFLAKE_USER}:{SNOWFLAKE_PASSWORD}@{SNOWFLAKE_ACCOUNT}/{SNOWFLAKE_DATABASE}/{SNOWFLAKE_SCHEMA}?warehouse={SNOWFLAKE_WAREHOUSE}"
logging.debug("🔗 Created Snowflake connection string")

# ========== Initialize SQLAlchemy Engine ==========
try:
    engine = create_engine(connection_string)
    logging.debug("✅ Snowflake engine created successfully")
except Exception as e:
    logging.error(f"❌ Failed to create Snowflake engine: {str(e)}")
    raise

# ========== Query Runner ==========
def run_query(query: str):
    """
    Executes a SQL query against Snowflake and returns results as a list of dictionaries.
    """
    try:
        logging.debug(f"📤 Running Snowflake query:\n{query.strip()}")
        with engine.connect() as conn:
            result = conn.execute(text(query))
            output = [dict(row._mapping) for row in result]
            logging.debug(f"✅ Query returned {len(output)} rows")
            return output
    except Exception as e:
        logging.error(f"❌ Snowflake query failed: {str(e)}")
        return []
