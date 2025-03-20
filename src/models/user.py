from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class UnavailabilityPeriod(BaseModel):
    start_time: datetime
    end_time: datetime


class Role(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(BaseModel):
    id: str = Field(..., alias="_id")
    email_address: str
    password: str
    role: Role


class Admin(User):
    role: str = Role.ADMIN


class Staff(User):
    first_name: str
    last_name: str
    contact_number: str
    specializations: List[str]
    department: str
    on_leave: bool = False
    unavailability_periods: List[UnavailabilityPeriod] = []
    license_id: str
    active: bool = True

    role: str = Role.DOCTOR


class Patient(User):
    role: str = Role.PATIENT
