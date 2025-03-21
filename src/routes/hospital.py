from __future__ import annotations

from fastapi import APIRouter, Request

from src.app import app, database
from src.models import CreateResponse, Hospital, UpdateResponse
from type import InsertOneResult

router = APIRouter(prefix="/admin", tags=["Admin"])

__all__ = ("router",)

ADMIN = None


@router.post("/hospital")
async def create_hospital(request: Request, data: Hospital) -> CreateResponse:
    """
    Create a new hospital.
    """
    collection = database["hospitals"]
    result: InsertOneResult = await collection.insert_one(dict(data))
    response = {"success": True, "inserted_id": str(result.inserted_id)}
    return CreateResponse(**response)


@router.patch("/hospital")
async def update_hospital(request: Request, data: Hospital) -> UpdateResponse:
    """
    Update hospital details.
    """
    collection = database["hospitals"]
    sendable_data = data.model_dump(mode="json")
    sendable_data["_id"] = sendable_data.pop("id")
    result = await collection.update_one({"_id": data.id}, {"$set": sendable_data})
    response = {"success": True, "modified_count": result.modified_count}
    return UpdateResponse(**response)


@router.get("/hospital/{hospital_or_admin_id}")
async def fetch_hospital_by_id(request: Request, hospital_or_admin_id: str) -> Hospital:
    """
    Fetch a hospital
    """
    collection = database["hospitals"]
    hospital = await collection.find_one(
        {"$or": [{"_id": hospital_or_admin_id}, {"admin_id": hospital_or_admin_id}]}
    )
    return Hospital.model_validate(hospital)


app.include_router(router)
