from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MedicalReport(BaseModel):
    id: str = Field(alias="_id")
    description: str
    date: str
    type: str
    image_data: Optional[bytes] = None
