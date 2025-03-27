from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class Hospital(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    address: str
    contact: str
    departments: List[str] = []
    specializations: List[str] = []
    admin_id: str
    announcements: List[Announcement] = []
    hospital_licence_number: str


class Announcement(BaseModel):
    title: str
    body: str
    created_at: datetime
