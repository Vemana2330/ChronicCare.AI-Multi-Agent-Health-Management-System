# FILE: postgres_db/models.py

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    # Personal info
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(String)

    # Health data
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    activity_level = Column(String)  # Sedentary, Lightly Active, etc.
    chronic_condition = Column(String)
    location = Column(String)

    # Derived metrics
    bmi = Column(Float)
    bmi_category = Column(String)
    tdee = Column(Float)

    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

class CalorieTracking(Base):
    __tablename__ = "calorie_tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    date = Column(Date)
    total_calories = Column(Float)
