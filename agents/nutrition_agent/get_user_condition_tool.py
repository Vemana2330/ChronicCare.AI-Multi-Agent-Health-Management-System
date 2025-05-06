# FILE: agents/nutrition_agent/get_user_condition_tool.py

import logging
from sqlalchemy.orm import Session
from langchain.tools import tool
from postgres_db.database import get_db
from postgres_db import models

# Optional: Configure logging here if not globally set
logger = logging.getLogger(__name__)

@tool
def get_user_condition(username: str) -> str:
    """
    🔍 Fetch the chronic condition of a given user from PostgreSQL.
    """
    logger.debug(f"🧑 Getting chronic condition for user: {username}")

    try:
        db: Session = next(get_db())
        logger.debug("✅ Database session acquired")

        user = db.query(models.User).filter(models.User.username == username).first()

        if user:
            logger.debug(f"🎯 Found user: {user.username} → Chronic Condition: {user.chronic_condition}")
            logger.debug(f"🔍 Checking user condition for username: {username}")
            return user.chronic_condition
        else:
            logger.warning("⚠️ User not found in database")
            return "User not found."
    except Exception as e:
        logger.error(f"❌ Error while fetching user condition: {str(e)}")
        return f"Error fetching user condition: {str(e)}"