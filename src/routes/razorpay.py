from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from razorpay.errors import SignatureVerificationError

from src.app import app, database, razorpay_client
from src.models import Appointment, Patient, Staff

router = APIRouter(tags=["Razorpay"], prefix="/razorpay-gateway")
from fastapi.responses import JSONResponse

cache: dict[str, Appointment] = {}


@router.post("/create-order-appointment")
async def rpay_order_appointment(appointment: Appointment):

    doctor_id = appointment.doctor_id
    doctor_data = await database["users"].find_one({"role": "doctor", "id": doctor_id})
    staff = Staff(**doctor_data)
    fees = staff.consultation_fee

    appointment_data = appointment.model_dump(mode="json")
    order_data = razorpay_client.payment_link.create(
        {
            "amount": max(fees * 100, 100),
            "currency": "INR",
            "notify": {"sms": True, "email": True},
            "accept_partial": False,
            "description": "Appointment Booking purpose",
            "notes": {
                "doctor_id": appointment.doctor_id,
                "patient_id": appointment.patient_id,
                "start_date": appointment.start_date,
                "end_date": appointment.end_date,
            },
            "callback_url": "http://13.233.139.216:8080/razorpay-gateway/verify-payment",
        }
    )
    order_id = order_data["id"]
    await database["appointments"].update_one(
        {"id": appointment.id}, {"$set": {"razorpay_order_data": order_data}}
    )
    cache[order_data["id"]] = appointment
    return order_data


@router.get("/verify-payment")
async def verify_payment(
    razorpay_payment_id: str,
    razorpay_payment_link_id: str,
    razorpay_payment_link_status: str,
    razorpay_signature: str,
):
    sendable = cache[razorpay_payment_link_id].model_dump(mode="json")
    sendable["_id"] = sendable["id"]
    sendable["razorpay_payment_id"] = razorpay_payment_link_id
    await database["appointments"].insert_one(sendable)

    return f"Payment {razorpay_payment_link_status == 'paid'}. You may now close this window."


@router.get("/bills/{admin_id}")
async def bills(admin_id: str):
    hospital_data = await database["hospitals"].find_one({"admin_id": admin_id})
    doctor_ids = []

    staffs = (
        await database["users"].find({"hospital_id": hospital_data["id"]}).to_list(100)
    )
    doctor_ids = [staff["id"] for staff in staffs]
    appointments = (
        await database["appointments"]
        .find(
            {"doctor_id": {"$in": doctor_ids}, "razorpay_payment_id": {"$exists": True}}
        )
        .to_list(100)
    )
    razorpay_payloads = []

    for appointmet in appointments:
        razorpay_payloads.append(
            razorpay_client.payment_link.fetch(appointmet["razorpay_payment_id"])
        )

    return razorpay_payloads

@router.get(
    "/bills/patient/{patient_id}",
)
async def patient_bills(patient_id: str):
    appointments = await database["appointments"].find(
        {"patient_id": patient_id, "razorpay_payment_id": {"$exists": True}}
    ).to_list(100)

    razorpay_payloads = []

    for appointmet in appointments:
        razorpay_payloads.append(
            razorpay_client.payment_link.fetch(appointmet["razorpay_payment_id"])
        )

    return razorpay_payloads


app.include_router(router)
