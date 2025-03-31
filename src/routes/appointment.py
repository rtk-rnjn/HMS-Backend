from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Appointment, Hospital, Staff
from src.utils import Authentication
from src.utils.email import send_smtp_email

router = APIRouter(tags=["Appointment"])


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
        temp_end_date = datetime.strptime(
            temp_appointment.end_date, date_format
        )
        temp_start_date = datetime.strptime(
            temp_appointment.start_date, date_format
        )

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
    print(appointments)

    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found")

    return [Appointment.model_validate(appointment) for appointment in appointments]


@router.websocket("/appointment/{appointment_id}/live")
async def live_appointment(appointment_id: str, websocket: WebSocket):
    await websocket.accept()
    while True:
        appointment = await database["appointments"].find_one({"_id": appointment_id})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        await websocket.send_json(Appointment.model_validate(appointment))
        await asyncio.sleep(5)


app.include_router(router)
