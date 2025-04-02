from __future__ import annotations

from pydantic import BaseModel, Field


class Review(BaseModel):
    id: str = Field(alias="_id")
    review: str
    patient_id: str
    doctor_id: str
    stars: int = 0
    created_at: str
