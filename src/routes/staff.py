from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Announcement, Hospital, Review, Role, Staff
from src.utils import Authentication
from src.utils.email import send_smtp_email

with open("src/utils/email-body-account-created.txt", "r") as f:
    EMAIL_BODY_ACCOUNT_CREATED = f.read()


class ClientRequest(BaseModel):
    data: dict


router = APIRouter(tags=["Staff"])


@router.post(
    "/staff/create",
    dependencies=[Depends(Authentication.access_required(Access.CREATE_STAFF))],
)
async def create_doctor(request: Request, staff: Staff):
    collection = database["users"]

    token = request.headers.get("Authorization").split(" ")[1]
    current_user = Authentication.get_current_user(token)

    user = await collection.find_one(
        {"email_address": staff.email_address, "role": "doctor"}
    )
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")

    admin = await collection.find_one({"email_address": current_user["sub"]})
    hospital = await database["hospitals"].find_one({"admin_id": admin["_id"]})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital_obj = Hospital.model_validate(hospital)

    sendable = staff.model_dump(mode="json")
    sendable["_id"] = sendable["id"]
    sendable["hospital_id"] = hospital_obj.id

    await asyncio.gather(
        send_smtp_email(
            sendable["email_address"],
            "Account Created",
            EMAIL_BODY_ACCOUNT_CREATED.format(
                sendable["email_address"], sendable["password"]
            ),
        ),
        collection.insert_one(sendable),
    )

    return Staff.model_validate(sendable)


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
    token = request.headers.get("Authorization").split(" ")[1]
    current_user = Authentication.get_current_user(token)

    admin = await collection.find_one({"email_address": current_user["sub"]})
    hospital = await database["hospitals"].find_one({"admin_id": admin["_id"]})

    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital_obj = Hospital.model_validate(hospital)

    staff = await collection.find(
        {"role": "doctor", "hospital_id": hospital_obj.id, "active": True}
    ).to_list(limit)
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
    await collection.update_one({"_id": doctor_id}, {"$set": {"active": False}})
    return True


@router.get(
    "/hospital/{admin_id}",
    dependencies=[Depends(Authentication.access_required(Access.READ_HOSPITAL))],
)
async def get_hospital(request: Request, admin_id: str) -> Hospital:
    collection = database["hospitals"]
    hospital = await collection.find_one({"admin_id": admin_id})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    return Hospital.model_validate(hospital)


@router.post(
    "/hospital/{admin_id}/create-announcement",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_HOSPITAL))],
)
async def create_announcement(request: Request, admin_id: str, announcement: dict):
    announcement = Announcement(**announcement)
    collection = database["hospitals"]
    hospital = await collection.find_one({"admin_id": admin_id})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    announcement_data = announcement.model_dump(mode="json")
    await collection.update_one(
        {"admin_id": admin_id},
        {"$addToSet": {"announcements": announcement_data}},
    )
    return {"success": True}


@router.post(
    "/hospital",
    dependencies=[Depends(Authentication.access_required(Access.CREATE_HOSPITAL))],
)
async def create_hospital(hospital: Hospital):
    collection = database["hospitals"]
    sendable_data = hospital.model_dump(mode="json")
    sendable_data["_id"] = hospital.id

    hospital = await collection.insert_one(sendable_data)
    return {"success": True}


@router.get(
    "/hospital/{admin_id}/announcements",
    dependencies=[Depends(Authentication.access_required(Access.READ_HOSPITAL))],
)
async def get_announcements(request: Request, admin_id: str) -> list[Announcement]:
    collection = database["hospitals"]
    hospital = await collection.find_one({"admin_id": admin_id})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital_obj = Hospital.model_validate(hospital)
    return hospital_obj.announcements


@router.get(
    "/hospital/{hospital_id}/doctors/announcements",
    dependencies=[Depends(Authentication.access_required(Access.READ_ANNOUNCEMENT))],
)
async def get_announcements_for_doctor(
    request: Request, hospital_id: str
) -> list[Announcement]:
    collection = database["hospitals"]
    hospital = await collection.find_one({"_id": hospital_id})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital_obj = Hospital.model_validate(hospital)
    return [
        announcement
        for announcement in hospital_obj.announcements
        if Role.STAFF in announcement.broadcast_to
    ]


@router.get(
    "/staffs",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def get_staff(request: Request, limit: int = 100) -> list[Staff]:
    collection = database["users"]

    staff = await collection.find({"role": "doctor", "active": True}).to_list(limit)
    return [Staff.model_validate(doctor) for doctor in staff]


@router.get(
    "/specializations",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def get_specializations(request: Request) -> list[str]:
    collection = database["users"]

    staff = await collection.find({"role": "doctor", "active": True}).to_list(100)
    return list(set([doctor["specialization"] for doctor in staff]))


@router.get(
    "/staff/{doctor_id}/average-rating",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def staff_average_rating(doctor_id: str):
    collection = database["reviews"]
    reviews_data = await collection.find(
        {"doctor_id": doctor_id},
    )

    reviews = [Review.model_validate(review) async for review in reviews_data]
    rating = sum(review.stars for review in reviews) / len(reviews)

    return {"rating": rating}


app.include_router(router)
