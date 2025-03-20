from __future__ import annotations

import random

from fastapi import APIRouter
from fastapi.requests import Request
from pydantic import BaseModel, EmailStr

from src.app import app
from src.models import BaseResponse
from src.utils.email import send_email

router = APIRouter(prefix="/utils", tags=["Utils"])

with open("src/utils/email-body-otp-requested.txt") as file:
    email_body = file.read()


class Email(BaseModel):
    recipient: str
    subject: str
    body: str


class RequestOTPResponse(BaseModel):
    email_address: str


class VerifyOTPResponse(BaseModel):
    email_address: str
    otp: str


class OTPHandler:
    # TTL Cache?

    otps = {}

    @classmethod
    def generate_otp(cls, id: str):
        otp = str(random.randint(100000, 999999))
        cls.otps[id] = otp
        return otp

    @classmethod
    def verify_otp(cls, id: str, otp: str) -> bool:
        if cls.otps.get(id) == otp:
            return True
        return False


@router.post("/send-email")
async def send_email_route(request: Request, email: Email) -> Email:
    """
    Send an email.
    """
    sent = await send_email(email.recipient, email.subject, email.body)
    return BaseResponse(success=sent)


@router.post("/generate-otp")
async def generate_otp(request: Request, client_response: RequestOTPResponse):
    """
    Generate a random 6-digit OTP.
    """
    email_address = client_response.email_address
    otp = OTPHandler.generate_otp(email_address)
    body = email_body.format(email_address, otp)
    sent = await send_email(email_address, "OTP Requested", body)
    return BaseResponse(success=sent)


@router.post("/verify-otp")
async def verify_otp(request: Request, client_response: VerifyOTPResponse):
    """
    Verify an OTP.
    """
    email_address = client_response.email_address
    otp = client_response.otp
    verified = OTPHandler.verify_otp(email_address, otp)
    return BaseResponse(success=verified)


app.include_router(router)
