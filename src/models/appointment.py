from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Appointment(BaseModel):
    id: str = Field(..., alias="_id")
    patient_id: str
    doctor_id: str
    start_date: str
    end_date: str
    status: str
    prescription: str = ""
    notes: str = ""
    reference: Optional[str] = None
    created_at: str
