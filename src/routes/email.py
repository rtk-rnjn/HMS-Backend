from __future__ import annotations

import asyncio
import os
import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException

from src.app import app
from src.utils.email import send_smtp_email

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]

with open("src/utils/email-body-otp-requested.txt", "r") as f:
    EMAIL_BODY_PASSWORD_RESET = f.read()

router = APIRouter(tags=["Email"])

otp_store = {}
OTP_EXPIRY_TIME = 300


@app.get("/email/send")
async def send_email(to_email: str, subject: str, body: str):
    if await send_smtp_email(to_email, subject, body):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Email sending failed")


@app.get("/request-otp")
async def request_otp(to_email: str):
    otp = random.randint(100000, 999999)
    otp_store[to_email] = (otp, time.time())
    email_body = EMAIL_BODY_PASSWORD_RESET.format(to_email, otp)

    if await send_smtp_email(to_email, "Your OTP Code", email_body):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@app.get("/verify-otp")
async def verify_otp(to_email: str, otp: int):
    if to_email not in otp_store:
        raise HTTPException(status_code=400, detail="OTP not found or expired")

    stored_otp, timestamp = otp_store[to_email]
    if time.time() - timestamp > OTP_EXPIRY_TIME:
        del otp_store[to_email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if stored_otp == otp:
        del otp_store[to_email]
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
