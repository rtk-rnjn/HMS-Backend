from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
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
    doctor_id = appointment.doctor_id
    doctor_data = await database["staff"].find_one({"_id": doctor_id})
    if not doctor_data:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor = Staff(**doctor_data)
    unavailability_periods = doctor.unavailability_periods
    start_date = datetime.fromisoformat(appointment.start_date)
    end_date = datetime.fromisoformat(appointment.end_date)

    for period in unavailability_periods:
        if start_date < period < end_date:
            raise HTTPException(
                status_code=400, detail="Doctor is unavailable at this time"
            )

    appointment_data = await database["appointments"].find_one(
        {"doctor_id": doctor_id, "start_date": appointment.start_date}
    )
    if appointment_data:
        raise HTTPException(
            status_code=400, detail="Doctor is already booked at this time"
        )

    appointment = appointment.model_dump(mode="json")
    await database["appointments"].insert_one(appointment)
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
