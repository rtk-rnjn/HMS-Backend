from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Patient, Staff
from src.utils import Authentication


class ClientRequest(BaseModel):
    data: dict


router = APIRouter(tags=["Patient"])


@router.post(
    "/patient/create",
)
async def create_patient(request: Request, client_request: ClientRequest):
    collection = database["users"]
    assert Staff(**client_request.data)
    await collection.insert_one(client_request.data)
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


app.include_router(router)
