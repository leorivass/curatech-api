from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class RegisterRequest(BaseModel):
    patient_first_name: str
    patient_last_name: str
    patient_birth_date: datetime
    patient_health_condition: Optional[str] = None
    caregiver_name: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    id_user: int
    patient_first_name: str
    patient_last_name: str
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic