from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Staff
from src.utils import Authentication


class ClientRequest(BaseModel):
    data: dict


router = APIRouter(tags=["Staff"])


@router.post(
    "/staff/create",
    dependencies=[Depends(Authentication.access_required(Access.CREATE_STAFF))],
)
async def create_doctor(request: Request, client_request: ClientRequest):
    collection = database["users"]
    assert Staff(**client_request.data)
    await collection.insert_one(client_request.data)

    return {"success": True}


@router.get(
    "/staff/{doctor_id}",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def get_doctor(doctor_id: str) -> Staff:
    collection = database["users"]
    doctor = await collection.find_one({"_id": doctor_id})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return Staff.model_validate(doctor)


@router.get(
    "/staff",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def get_staff(request: Request, limit: int = 100) -> list[Staff]:
    collection = database["users"]
    staff = await collection.find({"role": "doctor"}).to_list(limit)
    return [Staff.model_validate(doctor) for doctor in staff]


@router.put(
    "/staff/{doctor_id}",
    dependencies=[
        Depends(Authentication.access_required(Access.UPDATE_STAFF)),
        Depends(Authentication.access_required(Access.READ_STAFF)),
    ],
)
async def update_doctor(
    request: Request, doctor_id: str, client_request: ClientRequest
):
    collection = database["users"]
    assert Staff(**client_request.data)
    await collection.update_one({"_id": doctor_id}, {"$set": client_request.data})
    return {"success": True}


@router.delete(
    "/staff/{doctor_id}",
    dependencies=[Depends(Authentication.access_required(Access.DELETE_STAFF))],
)
async def delete_doctor(doctor_id: str):
    collection = database["users"]
    await collection.delete_one({"_id": doctor_id})
    return {"success": True}


app.include_router(router)
