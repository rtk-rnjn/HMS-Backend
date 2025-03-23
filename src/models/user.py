from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr

from src.models.enums import BloodGroup, Role


class UnavailabilityPeriod(BaseModel):
    start_time: datetime
    end_time: datetime


class UserBase(BaseModel):
    id: str = Field(..., alias="_id")
    email_address: EmailStr
    password: SecretStr
    role: Role

    class Config:
        from_attributes = True


class Admin(UserBase):
    role: str = Role.ADMIN


class Staff(UserBase):
    first_name: str
    last_name: Optional[str] = None
    contact_number: str
    specializations: List[str] = []
    department: str
    on_leave: bool = False
    unavailability_periods: List[UnavailabilityPeriod] = []
    license_id: str
    active: bool = True

    role: str = Role.STAFF
    hospital_id: str = ""


class Patient(UserBase):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: datetime
    blood_group: BloodGroup
    height: int
    weight: int
    allergies: List[str] = []
    medications: List[str] = []
    emergency_contact_name: str
    emergency_contact_number: str
    emergency_contact_relationship: str
    active: bool = True
    role: str = Role.PATIENT
