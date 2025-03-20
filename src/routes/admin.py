from __future__ import annotations

from fastapi import APIRouter, Request

from src.app import app, database
from src.models import CreateResponse, Staff, UpdateResponse
from src.utils import send_email
from type import InsertOneResult

router = APIRouter(prefix="/admin", tags=["Admin"])

__all__ = ("router",)

with open("src/utils/email-body-account-created.txt") as file:
    email_body = file.read()


@router.get("/staff/{staff_id}")
async def fetch_staff_by_id(request: Request, staff_id: str) -> Staff:
    """
    Fetch a staff member.
    """
    collection = database["users"]
    staff = await collection.find_one({"_id": staff_id})
    return Staff.model_validate(staff)


@router.get("/staff")
async def fetch_staff_by_email(
    request: Request, email_address: str, password: str
) -> Staff:
    """
    Fetch all staff members by department.
    """
    collection = database["users"]
    staff = await collection.find_one(
        {"email_address": email_address, "password": password}
    )
    return Staff(**staff)


@router.post("/staff")
async def create_staff(request: Request, staff: Staff) -> CreateResponse:
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
async def update_staff(request: Request, staff_id: str, staff: Staff) -> UpdateResponse:
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
async def delete_staff(request: Request, staff_id: str) -> UpdateResponse:
    """
    Delete a staff member.
    """
    collection = database["users"]
    result = await collection.update_one({"_id": staff_id}, {"$set": {"active": False}})
    return UpdateResponse(
        success=result.acknowledged, modified_count=result.modified_count
    )


app.include_router(router)
