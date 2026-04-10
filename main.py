from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from database import Base, engine, get_db
from models import User, Module, Device
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic, ModuleDetected, UpdateModuleData, PairDeviceWithUser, DevicePaired, ModulesResponse
from security import hash_password, verify_password, create_access_token

import time

app = FastAPI()

@app.post("/auth/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="This user is already registered")

    user = User(
        patient_first_name=payload.patient_first_name,
        patient_last_name=payload.patient_last_name,
        patient_birth_date=payload.patient_birth_date,
        patient_health_condition=payload.patient_health_condition,
        caregiver_name=payload.caregiver_name,
        email=payload.email,
        password_hash=payload.password,
        created_at=datetime.now(), 
    )
 
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserPublic(
        id_user=str(user.id_user),
        patient_first_name = user.patient_first_name,
        patient_last_name = user.patient_last_name,
        patient_birth_date = user.patient_birth_date,
        patient_health_condition = user.patient_health_condition,            
        caregiver_name = user.caregiver_name,
        email = user.email
    )

@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email, User.password_hash == payload.password)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")

    token = create_access_token(subject=str(user.id_user))

    return TokenResponse(
        access_token=token,
        user=UserPublic(
            id_user=str(user.id_user),
            patient_first_name = user.patient_first_name,
            patient_last_name = user.patient_last_name,
            patient_birth_date = user.patient_birth_date,
            patient_health_condition = user.patient_health_condition,
            caregiver_name = user.caregiver_name,
            email = user.email
        ),
    )

@app.get("/module/detect", response_model=ModuleDetected)
def detect_module(status: str, id_device: str, db: Session = Depends(get_db)):
    timeout = 20
    start = time.time()

    module = None

    while not module:
        module = db.execute(select(Module).where(Module.status == status, Module.id_device == id_device)).scalar_one_or_none()

        if module:
            break

        if time.time() - start > timeout:
            raise HTTPException(status_code=404, detail="Module not found")

        time.sleep(1)

    return ModuleDetected(
        servo_id=module.servo_id
    )

@app.patch("/module/update/{servo_id}/{id_device}", response_model=ModulesResponse)
def update_module_data(servo_id: int, id_device: str, payload: UpdateModuleData, db: Session = Depends(get_db)):
    module = db.execute(select(Module).where(Module.id_device == id_device, Module.servo_id == servo_id)).scalar_one_or_none()

    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found for this device and servo_id")

    if payload.pill_name is not None:
        module.pill_name = payload.pill_name
    if payload.dosage is not None:
        module.dosage = payload.dosage
    if payload.dose_times is not None:
        module.dose_times = payload.dose_times
    if payload.daily_qty is not None:
        if payload.daily_qty < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="daily_qty must be >= 1")
        module.daily_qty = payload.daily_qty
    if payload.notes is not None:
        module.notes = payload.notes
    if payload.status is not None:
        module.status = payload.status

    db.commit()

    modules = db.execute(select(Module).where(Module.id_device == id_device)).scalars().all()

    return {
        "ok": True, 
        "modules": modules
    }

@app.patch("/device/add", response_model=DevicePaired, status_code=201)
def register(payload: PairDeviceWithUser, db: Session = Depends(get_db)):
    device = db.execute(select(Device).where(Device.serial_number == payload.serial_number, Device.id_user == None)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=409, detail="This serial_number does not exist or is already paired with a user")

    if payload.id_user is not None:
        device.id_user = payload.id_user

    device.config_version = 0
 
    db.commit()

    return DevicePaired(
        id_device=str(device.id_device)
    )

