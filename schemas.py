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

class ModuleDetected(BaseModel):
    servo_id: int

class UpdateModuleData(BaseModel):
    pill_name: str
    dosage: str
    dose_times: list[str]
    daily_qty: int
    notes: str
    status: str

class PairDeviceWithUser(BaseModel):
    serial_number: str
    id_user: str

class DevicePaired(BaseModel):
    id_device: str

class ModuleOut(BaseModel):
    id_module: str
    servo_id: int
    pill_name: Optional[str] = None
    dosage: Optional[str] = None
    dose_times: Optional[list] = []
    daily_qty: Optional[int] = None
    notes: Optional[str] = None
 
    status: str
    id_device: str

class ModulesResponse(BaseModel):
    ok: bool

class AddModule(BaseModel):
    serial_number: str

class ModuleAdded(BaseModel):
    ok: bool
    servo_id: int

class ModuleScheduleOut(BaseModel):
    servo_id: int
    dose_times: list[str]
    status: str
    

