from __future__ import annotations

from enum import Enum


class Access(str, Enum):
    SUPER_ACCESS = "all"

    # Patient
    CREATE_PATIENT = "create:patient"
    READ_PATIENT = "read:patient"
    UPDATE_PATIENT = "update:patient"
    DELETE_PATIENT = "delete:patient"

    # Staff
    CREATE_STAFF = "create:staff"
    READ_STAFF = "read:staff"
    UPDATE_STAFF = "update:staff"
    DELETE_STAFF = "delete:staff"

    # Medical Records
    CREATE_MEDICAL_RECORD = "create:medical_record"
    READ_MEDICAL_RECORD = "read:medical_record"
    UPDATE_MEDICAL_RECORD = "update:medical_record"
    DELETE_MEDICAL_RECORD = "delete:medical_record"

    # Appointments
    CREATE_APPOINTMENT = "create:appointment"
    READ_APPOINTMENT = "read:appointment"
    UPDATE_APPOINTMENT = "update:appointment"
    DELETE_APPOINTMENT = "delete:appointment"

    # Payments
    CREATE_PAYMENT = "create:payment"
    READ_PAYMENT = "read:payment"
    UPDATE_PAYMENT = "update:payment"
    DELETE_PAYMENT = "delete:payment"

    # Admin
    UPDATE_ADMIN = "update:admin"

    # Hospital
    CREATE_HOSPITAL = "create:hospital"
    UPDATE_HOSPITAL = "update:hospital"
    READ_HOSPITAL = "read:hospital"
    DELETE_HOSPITAL = "delete:hospital"
    CREATE_HOSPITAL_ADMIN = "create:hospital_admin"


STAFF_ACCESS = [
    Access.CREATE_STAFF,
    Access.READ_STAFF,
    Access.UPDATE_STAFF,
    Access.CREATE_MEDICAL_RECORD,
    Access.READ_MEDICAL_RECORD,
    Access.UPDATE_MEDICAL_RECORD,
    Access.DELETE_MEDICAL_RECORD,
    Access.CREATE_APPOINTMENT,
    Access.READ_APPOINTMENT,
    Access.UPDATE_APPOINTMENT,
    Access.DELETE_APPOINTMENT,
    Access.CREATE_PAYMENT,
    Access.READ_PAYMENT,
    Access.UPDATE_PAYMENT,
    Access.DELETE_PAYMENT,
]

PATIENT_ACCESS = [
    Access.READ_STAFF,
    Access.CREATE_PATIENT,
    Access.READ_PATIENT,
    Access.UPDATE_PATIENT,
    Access.DELETE_PATIENT,
    Access.CREATE_MEDICAL_RECORD,
    Access.READ_MEDICAL_RECORD,
    Access.UPDATE_MEDICAL_RECORD,
    Access.DELETE_MEDICAL_RECORD,
    Access.CREATE_APPOINTMENT,
    Access.READ_APPOINTMENT,
    Access.UPDATE_APPOINTMENT,
    Access.DELETE_APPOINTMENT,
    Access.CREATE_PAYMENT,
    Access.READ_PAYMENT,
    Access.UPDATE_PAYMENT,
    Access.DELETE_PAYMENT,
]

ADMIN_ACCESS = [
    Access.SUPER_ACCESS,
    Access.CREATE_STAFF,
    Access.READ_STAFF,
    Access.UPDATE_STAFF,
    Access.DELETE_STAFF,
    Access.CREATE_PATIENT,
    Access.READ_PATIENT,
    Access.UPDATE_PATIENT,
    Access.DELETE_PATIENT,
    Access.CREATE_MEDICAL_RECORD,
    Access.READ_MEDICAL_RECORD,
    Access.UPDATE_MEDICAL_RECORD,
    Access.DELETE_MEDICAL_RECORD,
    Access.CREATE_APPOINTMENT,
    Access.READ_APPOINTMENT,
    Access.UPDATE_APPOINTMENT,
    Access.DELETE_APPOINTMENT,
    Access.CREATE_PAYMENT,
    Access.READ_PAYMENT,
    Access.UPDATE_PAYMENT,
    Access.DELETE_PAYMENT,
    Access.UPDATE_ADMIN,
    Access.CREATE_HOSPITAL,
    Access.UPDATE_HOSPITAL,
    Access.READ_HOSPITAL,
    Access.DELETE_HOSPITAL,
    Access.CREATE_HOSPITAL_ADMIN,
]
