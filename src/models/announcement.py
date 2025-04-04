from __future__ import annotations

import uuid

from pydantic import BaseModel
from typing import List

from .enums import AnnouncementCategory


class Announcement(BaseModel):
    title: str
    body: str
    created_at: str
    broadcast_to: str
    category: AnnouncementCategory


class LeaveRequest(BaseModel):
    id: str = str(uuid.uuid4())
    doctor_id: str
    reason: str
    approved: bool = False
    created_at: str
    dates: List[str]
