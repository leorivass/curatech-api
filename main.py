from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from database import Base, engine, get_db
from models import User  # tus modelos
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic
from security import hash_password, verify_password, create_access_token

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
        password_hash=hash_password(payload.password),
        created_at=datetime.utcnow(), 
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserPublic(
        id_user=user.id_user,
        patient_first_name=user.patient_first_name,
        patient_last_name=user.patient_last_name,
        email=user.email,
    )

@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = create_access_token(subject=str(user.id_user))

    return TokenResponse(
        access_token=token,
        user=UserPublic(
            id_user=user.id_user,
            patient_first_name=user.patient_first_name,
            patient_last_name=user.patient_last_name,
            email=user.email,
        ),
    )