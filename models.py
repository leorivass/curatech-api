from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base

class User(Base):
    __tablename__ = 'users'
    
    id_user = Column(Integer, primary_key=True)
    patient_first_name = Column(String, nullable=False)
    patient_last_name = Column(String, nullable=False)
    patient_birth_date = Column(DateTime, nullable=False)
    patient_health_condition = Column(String)
    caregiver_name = Column(String)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
class Device(Base):
    __tablename__ = 'devices'
    
    id_device = Column(Integer, primary_key=True)
    serial_number = Column(String, unique=True, nullable=False)
    api_key_hash = Column(String, nullable=False)
    config_version = Column(Integer, nullable=False, default=0)
    id_user = Column(Integer, ForeignKey('user.id_user', ondelete='CASCADE'), nullable=False)
    
class Module(Base):
    __tablename__ = 'modules'
    
    id_module = Column(Integer, primary_key=True)
    servo_id = Column(Integer, nullable=False)
    pill_name = Column(String, nullable=False)
    dosage = Column(String)
    dose_times = Column(String, nullable=False)
    daily_qty = Column(Integer, nullable=False)
    notes = Column(String)
    status = Column(String, nullable=False)
    id_device = Column(Integer, ForeignKey('device.id_device', ondelete='CASCADE'), nullable=False)