from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.enums import BloodGroup, Role


class UnavailabilityPeriod(BaseModel):
    start_time: datetime
    end_time: datetime


class UserBase(BaseModel):
    id: str = Field(..., alias="_id")
    email_address: str
    password: str
    role: Role

    class Config:
        from_attributes = True


class Admin(UserBase):
    role: str = Role.ADMIN


class Staff(UserBase):
    first_name: str
    last_name: Optional[str] = None
    gender: str = "Other"
    contact_number: str
    date_of_birth: datetime
    specializations: List[str] = []
    department: str
    on_leave: bool = False
    consultation_fee: int = 0
    unavailability_periods: List[UnavailabilityPeriod] = []
    license_id: str
    year_of_experience: int = 0
    active: bool = True
    joining_date: str
    role: str = Role.STAFF
    hospital_id: str = ""


class Patient(UserBase):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: datetime
    gender: str = "Other"
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
