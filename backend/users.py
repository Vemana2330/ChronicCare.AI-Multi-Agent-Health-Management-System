# FILE: backend/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated
import logging
import traceback
from pydantic import BaseModel

from postgres_db import schemas
from postgres_db.database import get_db
from postgres_db import auth, models

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Password change schema
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

def calculate_bmi(height_cm: float, weight_kg: float):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 25:
        category = "Normal weight"
    elif 25 <= bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return round(bmi, 2), category

def get_activity_factor(activity_level: str) -> float:
    activity_map = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }
    return activity_map.get(activity_level, 1.2)

def calculate_tdee(age: int, gender: str, height_cm: float, weight_kg: float, activity_level: str, condition: str):
    # Mifflin-St Jeor BMR formula
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_factor = get_activity_factor(activity_level)
    tdee = bmr * activity_factor

    # Adjust based on chronic condition
    if condition.lower() == "obesity":
        tdee *= 0.85
    elif condition.lower() == "type2":
        tdee *= 0.90
    elif condition.lower() == "ckd":
        # Use per kg method
        tdee = 30 * weight_kg  # Or 35 based on stage, simplified here
    elif condition.lower() == "polycystic":
        tdee *= 0.85
    # Else leave unchanged for Hypertension, Cholesterol, Gluten

    return round(tdee, 2)

@router.post("/signup", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.debug(f"Attempting to create user: {user.username}")
        
        if auth.get_user(db, username=user.username):
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = auth.get_password_hash(user.password)
        
        # Calculate BMI and category
        bmi, bmi_category = calculate_bmi(user.height, user.weight)

        # Calculate TDEE
        tdee = calculate_tdee(
            age=user.age,
            gender=user.gender,
            height_cm=user.height,
            weight_kg=user.weight,
            activity_level=user.activity_level,
            condition=user.chronic_condition
        )

        db_user = models.User(
            username=user.username,
            password=hashed_password,
            chronic_condition=user.chronic_condition,
            location=user.location,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            age=user.age,
            gender=user.gender,
            height=user.height,
            weight=user.weight,
            activity_level=user.activity_level,
            bmi=bmi,
            bmi_category=bmi_category,
            tdee=tdee
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User {user.username} created successfully with BMI={bmi} and TDEE={tdee}")
        return db_user

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating user: {str(e)}"
        )

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    try:
        user = auth.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user = Depends(auth.get_current_active_user)
):
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        if not auth.verify_password(password_data.current_password, current_user.password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        current_user.password = auth.get_password_hash(password_data.new_password)
        db.commit()
        return {"detail": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Password update failed: {str(e)}"
        )
