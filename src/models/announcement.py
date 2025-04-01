from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import AnnouncementCategory


class Announcement(BaseModel):
    title: str
    body: str
    created_at: str
    broadcast_to: str
    category: AnnouncementCategory
