from __future__ import annotations

from enum import Enum


class AnnouncementCategory(str, Enum):
    GENERAL = "General"
    EMERGENCY = "Emergency"
    APPOINTMENT = "Appointment"
    HOLIDAY = "Holiday"
