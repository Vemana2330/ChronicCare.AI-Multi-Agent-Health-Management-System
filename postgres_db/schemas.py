# FILE: postgres_db/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ========== BASE SCHEMA ==========

class UserBase(BaseModel):
    username: str
    chronic_condition: str
    location: str

    # ✅ Newly added fields
    first_name: str
    last_name: str
    email: EmailStr
    age: int
    gender: str  # "Male" or "Female"
    height: float  # in cm
    weight: float  # in kg
    activity_level: str  # e.g., Sedentary, Lightly Active, etc.

# ========== INPUT SCHEMA (SIGN UP) ==========

class UserCreate(UserBase):
    password: str

# ========== OUTPUT SCHEMA ==========

class User(UserBase):
    id: int
    is_active: bool

    # ✅ Include derived fields
    bmi: float
    bmi_category: str
    tdee: float

    class Config:
        from_attributes = True

# ========== AUTH SCHEMAS ==========

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
