from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from database import Base, engine, get_db
from models import User, Module, Device
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic, ModuleDetected, UpdateModuleData
from security import hash_password, verify_password, create_access_token

import time

app = FastAPI()

@app.post("/auth/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email ya registrado")

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

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

@app.get("/detect/module", response_model=ModuleDetected)
def detect_module(status: str, id_device: int, db: Session = Depends(get_db)):
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

@app.patch("/update/module/{servo_id}")
def update_module_data(servo_id: int, payload: UpdateModuleData, db: Session = Depends(get_db)):
    module = db.execute(select(Module).where(Module.servo_id == servo_id)).scalar_one_or_none()

    if not module:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Module with this servo_id not found")
    
    if module.pill_name is not None:
        module.pill_name = payload.pill_name

    if module.dosage is not None:
        module.dosage = payload.dosage

    if module.dose_times is not None:
        module.dose_times = payload.dose_times

    if module.daily_qty is not None:
        if payload.daily_qty < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Daily quantity must be greater than 0")
        module.daily_qty = payload.daily_qty

    if module.notes is not None:
        module.notes = payload.notes

    if module.status is not None:
        module.status = "TAKEN"

    db.commit()
    db.refresh(module)
    
    return 0

