from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Announcement, Appointment, Patient, Role, Staff
from src.utils import Authentication
from src.utils.email import send_smtp_email

router = APIRouter(tags=["Appointment"])


async def log(admin_id: str, message: str):
    collection = database["hospitals"]
    await collection.update_one(
        {"admin_id": admin_id},
        {
            "$addToSet": {
                "logs": {
                    "message": message,
                    "created_at": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                }
            }
        },
    )


@router.post(
    "/appointment/create",
    dependencies=[Depends(Authentication.access_required(Access.CREATE_APPOINTMENT))],
)
async def create_appointment(request: Request, appointment: Appointment):
    # appointment = Appointment(**appointment)
    appointment_collection = database["appointments"]

    async for appointment_data in appointment_collection.find(
        {"doctor_id": appointment.doctor_id}
    ):
        temp_appointment = Appointment(**appointment_data)

        # Sample DateTime: 2025-04-02T06:30:00Z
        # Convert to datetime objects
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        temp_end_date = datetime.strptime(temp_appointment.end_date, date_format)
        temp_start_date = datetime.strptime(temp_appointment.start_date, date_format)

        start_date = datetime.strptime(appointment.start_date, date_format)
        end_date = datetime.strptime(appointment.end_date, date_format)

        if start_date < temp_end_date and end_date > temp_start_date:
            raise HTTPException(
                status_code=400, detail="Doctor is already booked for this time"
            )

    doctor = await database["users"].find_one({"_id": appointment.doctor_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    patient = await database["users"].find_one({"_id": appointment.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appointment_data = appointment.model_dump(mode="json")
    appointment_data["_id"] = appointment_data["id"]
    appointment_data["doctor_id"] = doctor["id"]
    appointment_data["patient_id"] = patient["id"]

    await appointment_collection.insert_one(appointment_data)

    staff = await database["users"].find_one({"_id": doctor["id"]})
    hospital = await database["hospital"].find_one({"id": staff["hospital_id"]})

    # await log(hospital["admin_id"], f'{staff["first_name"]}')

    return {"success": True}


@router.get(
    "/appointment/{appointment_id}",
    dependencies=[Depends(Authentication.access_required(Access.READ_APPOINTMENT))],
)
async def get_appointment(appointment_id: str):
    appointment = await database["appointments"].find_one({"_id": appointment_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment.model_validate(appointment)


@router.put(
    "/appointment/{appointment_id}",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_APPOINTMENT))],
)
async def update_appointment(appointment_id: str, appointment: Appointment):
    appointment_data = await database["appointments"].find_one({"_id": appointment_id})
    if not appointment_data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await database["appointments"].update_one(
        {"_id": appointment_id}, {"$set": appointment.model_dump(mode="json")}
    )
    return {"success": True}


@router.get(
    "/appointments/{doctor_id_or_patient_id}",
    dependencies=[Depends(Authentication.access_required(Access.READ_APPOINTMENT))],
)
async def get_appointments(doctor_id_or_patient_id: str, completed: bool = False):
    appointments = (
        await database["appointments"]
        .find(
            {
                "$or": [
                    {"doctor_id": doctor_id_or_patient_id},
                    {"patient_id": doctor_id_or_patient_id},
                ]
            }
        )
        .to_list(length=100)
    )

    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found")

    return [Appointment.model_validate(appointment) for appointment in appointments]


@router.delete(
    "/appointment/{appointment_id}/cancel",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_APPOINTMENT))],
)
async def cancel_appointment(appointment_id: str):

    appointment = await database["appointments"].find_one({"_id": appointment_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    await database["appointments"].update_one(
        {"_id": appointment_id}, {"$set": {"cancelled": True}}
    )

    patient_data = await database["users"].find_one({"_id": appointment["patient_id"]})
    staff_data = await database["users"].find_one({"_id": appointment["doctor_id"]})
    staff = Staff(**staff_data)
    patient = Patient(**patient_data)

    if patient:
        await send_smtp_email(
            subject="Appointment Cancelled",
            body=f"Your appointment with {staff.first_name} {staff.last_name} has been cancelled.",
            to=patient.email_address,
        )

    hospital = await database["hospitals"].find_one({"_id": staff.hospital_id})
    await log(
        hospital["admin_id"],
        f"{patient.first_name} cancelled appointment with {staff.first_name}",
    )

    return {"success": True}


@router.patch(
    "/appointment/{appointment_id}/mark-as-done",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_APPOINTMENT))],
)
async def mark_appointment_as_done(appointment: Appointment):
    await database["appointments"].update_one(
        {"_id": appointment.id}, {"$set": {"status": "Completed"}}
    )

    collection = database["users"]
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.now(timezone.utc)
    date_string = now.strftime(date_format)

    announcement = Announcement(
        title="Appointment Updated",
        body="Your appointment is completed, and marked as done.",
        created_at=date_string,
        broadcast_to=[Role.PATIENT],
        category="General",
    )
    announcement_data = announcement.model_dump(mode="json")

    await collection.update_one(
        {"_id": appointment["patient_id"]},
        {"$addToSet": {"announcements": announcement_data}},
    )

    return {"success": True}


app.include_router(router)
