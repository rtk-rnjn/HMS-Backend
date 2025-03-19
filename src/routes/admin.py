from __future__ import annotations

from fastapi import APIRouter, Request

from src import database
from src.models import CreateResponse, Staff, UpdateResponse
from src.utils import send_email
from type import InsertOneResult

router = APIRouter(prefix="/admin", tags=["Admin"])

__all__ = ("router",)

with open("src/utils/email-body.txt") as file:
    email_body = file.read()


@router.post("/staff")
async def create_staff(request: Request, staff: Staff) -> Staff:
    """
    Create a new staff member.
    """
    collection = database["users"]
    sendable_data = staff.model_dump(mode="json")

    sendable_data["_id"] = sendable_data.pop("id")

    result: InsertOneResult = await collection.insert_one(sendable_data)

    response = {"success": True, "inserted_id": str(result.inserted_id)}

    body = email_body.format(staff.name, staff.email_address, staff.password)
    await send_email(staff.email_address, "Account Created", body)

    return CreateResponse(**response)


@router.patch("/staff/{staff_id}")
async def update_staff(request: Request, staff_id: str, staff: Staff) -> Staff:
    """
    Update a staff member.
    """
    collection = database["users"]
    sendable_data = staff.model_dump(mode="json")

    result = await collection.update_one({"_id": staff_id}, {"$set": sendable_data})
    return UpdateResponse(
        success=result.acknowledged, modified_count=result.modified_count
    )


@router.delete("/delete/staff/{staff_id}")
async def delete_staff(request: Request, staff_id: str) -> Staff:
    """
    Delete a staff member.
    """
    collection = database["users"]
    result = await collection.delete_one({"_id": staff_id})
    return UpdateResponse(
        success=result.acknowledged, modified_count=result.deleted_count
    )
