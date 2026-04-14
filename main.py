from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, time as dt_time

from database import Base, engine, get_db
from models import User, Module, Device
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic, ModuleDetected, UpdateModuleData, PairDeviceWithUser, DevicePaired, ModulesResponse, ModuleOut, AddModule, ModuleAdded, ModuleScheduleOut
from security import hash_password, verify_password, create_access_token

import time as py_time

app = FastAPI()

def parse_times(times: list[str]) -> list[dt_time]:
    return [dt_time.fromisoformat(t) for t in times]

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
    start = py_time.time()

    module = None

    while not module:
        module = db.execute(select(Module).where(Module.status == status, Module.id_device == id_device)).scalar_one_or_none()

        if module:
            break

        if py_time.time() - start > timeout:
            raise HTTPException(status_code=404, detail="Module not found")

        py_time.sleep(1)

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
        module.dose_times = parse_times(payload.dose_times)
    if payload.daily_qty is not None:
        if payload.daily_qty < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="daily_qty must be >= 1")
        module.daily_qty = payload.daily_qty
    if payload.notes is not None:
        module.notes = payload.notes
    if payload.status is not None:
        module.status = payload.status

    db.commit()

    return {
        "ok": True, 
    }

@app.patch("/device/add", response_model=DevicePaired, status_code=201)
def add_device(payload: PairDeviceWithUser, db: Session = Depends(get_db)):
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

@app.get("/module/get/{id_device}", response_model=list[ModuleOut])
def get_all_modules(id_device: str, db: Session = Depends(get_db)):
    modules = db.execute(select(Module).where(Module.id_device == id_device)).scalars().all()

    if not modules:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No modules found for this device")

    return [ModuleOut(
        id_module=str(module.id_module),
        servo_id=module.servo_id,
        pill_name=module.pill_name,
        dosage=module.dosage,
        dose_times=module.dose_times,
        daily_qty=module.daily_qty,
        notes=module.notes,
        status=module.status,
        id_device=str(module.id_device)
    ) for module in modules]

@app.post("/module/add", response_model=ModuleAdded, status_code=200)
def add_module(payload: AddModule, db: Session = Depends(get_db)):
    new_servo_id = None;

    device = db.execute(select(Device).where(Device.serial_number == payload.serial_number)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This device does not exist")

    last_module_added = db.execute(select(Module).where(Module.id_device == device.id_device).order_by(Module.servo_id.desc()).limit(1)).scalar_one_or_none()
    if not last_module_added:
        new_servo_id = 2
    else:
        new_servo_id = last_module_added.servo_id + 1

    module = Module(
        servo_id = new_servo_id,
        pill_name = None,
        dosage = None,
        dose_times = None,
        daily_qty = None,
        notes = None,
        status = "PENDING",
        id_device = device.id_device
    )

    db.add(module)
    db.commit()
    db.refresh(module)

    return {
        "ok": True,
        "servo_id": module.servo_id
    }

@app.get("/device/schedule/{serial_number}", response_model=list[ModuleScheduleOut])
def get_device_schedule(serial_number: str, db: Session = Depends(get_db)):
    device = db.execute(
        select(Device).where(Device.serial_number == serial_number)
    ).scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    modules = db.execute(
        select(Module).where(
            Module.id_device == device.id_device,
            Module.servo_id != None,     # evita PENDING sin servo_id
            Module.dose_times != None    # evita módulos sin horas
        )
    ).scalars().all()

    return [
        ModuleScheduleOut(
            servo_id=m.servo_id,
            dose_times=[t.strftime("%H:%M:%S") for t in (m.dose_times or [])],
            status=m.status
        )
        for m in modules
    ]
    

