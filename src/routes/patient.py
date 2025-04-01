from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Announcement, Patient, Staff
from src.utils import Authentication
import uuid


class ClientRequest(BaseModel):
    data: dict


router = APIRouter(tags=["Patient"])


@router.post(
    "/patient/create",
)
async def create_patient(request: Request, patient: Patient):
    collection = database["users"]
    sendable = patient.model_dump(mode="json")
    sendable["_id"] = sendable["id"]

    user = await collection.find_one(
        {"email_address": sendable["email_address"], "role": "patient"}
    )
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")

    await collection.insert_one(sendable)
    return {"success": True}


@router.get(
    "/patient/{patient_id}",
    dependencies=[Depends(Authentication.access_required(Access.READ_PATIENT))],
)
async def get_patient(patient_id: str) -> Patient:
    collection = database["users"]
    patient = await collection.find_one({"_id": patient_id})
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return Patient.model_validate(patient)


@router.put(
    "/patient/{patient_id}",
    dependencies=[
        Depends(Authentication.access_required(Access.UPDATE_PATIENT)),
        Depends(Authentication.access_required(Access.READ_PATIENT)),
    ],
)
async def update_patient(
    patient_id: str, request: Request, client_request: ClientRequest
):
    collection = database["users"]
    await collection.update_one({"_id": patient_id}, {"$set": client_request.data})
    return {"success": True}


@router.delete(
    "/patient/{patient_id}",
    dependencies=[Depends(Authentication.access_required(Access.DELETE_PATIENT))],
)
async def delete_patient(patient_id: str):
    collection = database["users"]
    await collection.delete_one({"_id": patient_id})
    return {"success": True}


@router.post(
    "/patient/{patient_id}/prescription",
    dependencies=[
        Depends(Authentication.access_required(Access.CREATE_MEDICAL_RECORD))
    ],
)
async def create_prescription(patient_id: str, data: dict):
    collection = database["prescriptions"]
    data["_id"] = data.get("id", str(uuid.uuid4()))
    data["patient_id"] = patient_id

    await collection.insert_one(data)

    return {"success": True}


@router.get(
    "/patient/{patient_id}/prescription",
    dependencies=[Depends(Authentication.access_required(Access.READ_MEDICAL_RECORD))],
)
async def get_prescription(patient_id: str):
    collection = database["prescriptions"]
    prescriptions = await collection.find({"patient_id": patient_id}).to_list(
        length=100
    )
    if prescriptions is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescriptions


@router.put(
    "/patient/{patient_id}/prescription",
    dependencies=[
        Depends(Authentication.access_required(Access.UPDATE_MEDICAL_RECORD))
    ],
)
async def update_prescription(patient_id: str, data: dict):
    collection = database["prescriptions"]
    await collection.update_one({"patient_id": patient_id}, {"$set": data})
    return {"success": True}


@router.get(
    "/patient/{patient_id}/announcements/",
    dependencies=[Depends(Authentication.access_required(Access.READ_ANNOUNCEMENT))],
)
async def get_announcement(patient_id: str):
    collection = database["hospitals"]
    announcements = collection.find(
        {"announcements.broadcast_to": "patient"}, {"announcements.$": 1}
    ).to_list(length=100)
    return [Announcement.model_validate(announcement) for announcement in announcements]


@router.post(
    "/patient/{patient_id}/medical-report",
    dependencies=[
        Depends(Authentication.access_required(Access.CREATE_MEDICAL_RECORD))
    ],
)
async def create_medical_report(patient_id: str, data: dict):
    collection = database["medical_reports"]
    data["_id"] = data.get("id", str(uuid.uuid4()))
    data["patient_id"] = patient_id

    await collection.insert_one(data)
    return {"success": True}


@router.get(
    "/patient/{patient_id}/medical-reports",
    dependencies=[Depends(Authentication.access_required(Access.READ_MEDICAL_RECORD))],
)
async def get_medical_report(patient_id: str):
    collection = database["medical_reports"]
    medical_reports = await collection.find({"patient_id": patient_id}).to_list(
        length=100
    )
    return [dict(medical_report) for medical_report in medical_reports]


app.include_router(router)
