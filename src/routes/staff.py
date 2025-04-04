from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from pydantic import BaseModel

from src.app import app, database
from src.models import Access, Announcement, Hospital, LeaveRequest, Review, Role, Staff, Patient
from src.utils import Authentication
from src.utils.email import send_smtp_email
import uuid

with open("src/utils/email-body-account-created.txt", "r") as f:
    EMAIL_BODY_ACCOUNT_CREATED = f.read()


class ClientRequest(BaseModel):
    data: dict


router = APIRouter(tags=["Staff"])


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


@router.get("/hospital/{admin_id}/logs")
async def fetch_hospital_logs(admin_id: str):
    collection = database["hospitals"]
    hospital_data = await collection.find_one({"admin_id": admin_id})
    return hospital_data.get("logs")


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
        log(hospital["admin_id"], f"You added doctor: {staff.first_name}"),
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


@router.post(
    "/staff/{doctor_id}/leave-request",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_STAFF))],
)
async def apply_for_request(leave_request: LeaveRequest):
    collection = database["leave_requests"]
    await collection.insert_one(
        {
            "_id": leave_request.id,
            "doctor_id": leave_request.doctor_id,
            "dates": leave_request.dates,
            "reason": leave_request.reason,
            "approved": leave_request.approved,
            "created_at": leave_request.created_at
        },
    )

    return {"success": True}


@router.get(
    "/staff/{doctor_id}/leave-request",
    dependencies=[Depends(Authentication.access_required(Access.READ_STAFF))],
)
async def get_leave_request(doctor_id: str):
    collection = database["leave_requests"]
    leave_requests = await collection.find({"doctor_id": doctor_id}).to_list(100)

    requests = []
    for leave_request in leave_requests:

        requests.append(LeaveRequest(**leave_request))

    return requests

@router.patch(
    "/staff/leave-request",
    dependencies=[Depends(Authentication.access_required(Access.UPDATE_STAFF))],
)
async def approve_request(leave_request: LeaveRequest):
    collection = database["leave_requests"]

    data = await collection.update_one(
        {"doctor_id": leave_request.doctor_id}, {"$set": {"approved": True}}
    )
    staff = await collection.find_one(
        {"_id": leave_request.doctor_id}
    )

    try:
        await send_smtp_email(
            to_email=staff["email_address"],
            subject="Leave Approved",
            body=f"Admin approved your leave request.",
        )
    except Exception:
        pass

    updated_request = await collection.find_one(
        {"doctor_id": leave_request.doctor_id}
    )

    appointments = await database["appointments"].find({"doctor_id": leave_request.doctor_id}).to_list(100)
    leave_dates = {date_string[:10] for date_string in updated_request["dates"]}

    print("Leave Dates", leave_dates)

    for date_string in updated_request["dates"]:
        # Date String: "%Y-%m-%dT%H:%M:%SZ"

        for appointment_data in appointments:
            start_date_string = appointment_data["start_date"]
            start_date_only = start_date_string[:10]
            print("Start date", start_date_only)
            if start_date_only in leave_dates:
                appointment = await database["appointments"].find_one({"_id": appointment_data["_id"], "razorpay_payment_id": {"$exists": True}})
                if not appointment:
                    raise HTTPException(status_code=404, detail="Appointment not found")

                await database["appointments"].update_one(
                    {"_id": appointment_data["_id"]}, {"$set": {"cancelled": True, "doctor_id": "", "patient_id": ""}}
                )

                # razorpay_client.payment.refund("pay_" + appointment["razorpay_payment_id"].split("_")[1])

                try:
                    patient_data = await database["users"].find_one({"_id": appointment["patient_id"]})
                    patient = Patient(**patient_data)

                    if patient:
                        await send_smtp_email(
                            to_email=patient.email_address,
                            subject="Appointment Cancelled",
                            body=f"Your appointment with has been cancelled. Refund initiated.",
                        )
                except Exception:
                    pass

    return {"success": True}


@router.get(
    "/hospital/{admin_id}/leave-requests"
)
async def fetch_leave_requests(admin_id: str):
    hospital_data = await database["hospitals"].find_one({"admin_id": admin_id})
    hospital_id = hospital_data["id"]

    staffs = await database["users"].find({"hospital_id": hospital_id}).to_list(100)
    staff_ids = [staff["id"] for staff in staffs]

    leave_requests = await database["leave_requests"].find({"doctor_id": {"$in": staff_ids}}).to_list(100)

    return leave_requests

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
    doctor = await collection.find_one({"_id": doctor_id})
    staff = Staff(**doctor)
    hospital_data = await database["hospitals"].find_one({"id": staff.hospital_id})
    hospital = Hospital(**hospital_data)

    await log(hospital.admin_id, f"{staff.first_name} got deleted from system")

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
async def create_announcement(
    request: Request, admin_id: str, announcement: Announcement
):
    collection = database["hospitals"]
    hospital = await collection.find_one({"admin_id": admin_id})
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    announcement_data = announcement.model_dump(mode="json")
    await collection.update_one(
        {"admin_id": admin_id},
        {"$addToSet": {"announcements": announcement_data}},
    )

    await log(admin_id, "You created announcement")

    return {"success": True}


@router.post(
    "/hospital",
    dependencies=[Depends(Authentication.access_required(Access.CREATE_HOSPITAL))],
)
async def create_hospital(hospital: Hospital):
    collection = database["hospitals"]
    sendable_data = hospital.model_dump(mode="json")
    sendable_data["_id"] = hospital.id

    await collection.insert_one(sendable_data)
    await log(hospital.admin_id, f"You onboarded Hospital: {hospital.name}")
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
    ).to_list(100)

    reviews = [Review.model_validate(review) for review in reviews_data]
    rating = sum(review.stars for review in reviews) / max(len(reviews), 1)

    return {"rating": rating}


app.include_router(router)
