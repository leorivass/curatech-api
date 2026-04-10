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
    id_user: str
    patient_first_name: str
    patient_last_name: str
    patient_birth_date: datetime
    patient_health_condition: Optional[str] = None
    caregiver_name: Optional[str] = None
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

# class DetectModule(BaseModel):
#     status: str
#     id_device: str

class ModuleDetected(BaseModel):
    servo_id: int

class UpdateModuleData(BaseModel):
    pill_name: str
    dosage: str
    dose_times: list
    daily_qty: int
    notes: str

class PairDeviceWithUser(BaseModel):
    serial_number: str
    id_user: str

class DevicePaired(BaseModel):
    id_device: str

class ModuleOut(BaseModel):
    id_module: int
    servo_id: int
    pill_name: str
    dosage: Optional[str] = None
    dose_times: list[str]
    daily_qty: int
    notes: Optional[str] = None
    status: str
    id_device: str

class ModulesResponse(BaseModel):
    ok: bool
    modules: list[ModuleOut]

    

