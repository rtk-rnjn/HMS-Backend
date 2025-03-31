from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class Appointment(BaseModel):
    id: str = Field(..., alias="_id")
    patient_id: str
    doctor_id: str
    start_date: str
    end_date: str
    status: AppointmentStatus
    prescription: str = ""
    notes: str = ""
    reference: Optional[str] = None
    created_at: str
