from __future__ import annotations

from enum import Enum

from .access import ADMIN_ACCESS, PATIENT_ACCESS, STAFF_ACCESS


class Role(str, Enum):
    ADMIN = "admin"
    STAFF = "doctor"
    PATIENT = "patient"

    @staticmethod
    def get_access(role: Role) -> list[str]:
        if role == Role.ADMIN:
            return ADMIN_ACCESS

        if role == Role.STAFF:
            return STAFF_ACCESS

        if role == Role.PATIENT:
            return PATIENT_ACCESS

        return []
