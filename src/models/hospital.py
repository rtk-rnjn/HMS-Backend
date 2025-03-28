from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Union

from pydantic import BaseModel, Field

from src.models import Role


class Hospital(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    address: str
    contact: str
    departments: List[str] = []
    specializations: List[str] = []
    admin_id: str
    announcements: List[Announcement] = []
    hospital_licence_number: str = ""
    latitude: float
    longitude: float


class Announcement(BaseModel):
    title: str
    body: str
    created_at: datetime
    broadcast_to: List[Role] = []
    category: str = "General"


class AnnouncementCategory(str, Enum):
    GENERAL = "General"
    EMERGENCY = "Emergency"
    APPOINTMENT = "Appointment"
    HOLIDAY = "Holiday"
