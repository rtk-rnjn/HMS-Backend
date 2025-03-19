from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(BaseModel):
    id: int = Field(..., alias="_id")
    email_address: str
    password: str


class Admin(User):
    role: str = Role.ADMIN


class Doctor(User):
    role: str = Role.DOCTOR


class Patient(User):
    role: str = Role.PATIENT
