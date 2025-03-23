from __future__ import annotations

import os
import smtplib
import random
import time
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, HTTPException, Depends
from src.app import app

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]

with open("src/utils/email-body-account-created.txt", "r") as f:
    EMAIL_BODY_ACCOUNT_CREATED = f.read()

with open("src/utils/email-body-otp-requested.txt", "r") as f:
    EMAIL_BODY_PASSWORD_RESET = f.read()

router = APIRouter(tags=["Email"])

otp_store = {}
OTP_EXPIRY_TIME = 300


async def send_smtp_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sync_send_email, msg, to_email)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def sync_send_email(msg, to_email):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Sync email sending failed: {e}")


@app.post("/email/send")
async def send_email(to_email: str, subject: str, body: str):
    if await send_smtp_email(to_email, subject, body):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Email sending failed")


@app.post("/request-otp")
async def request_otp(to_email: str):
    otp = random.randint(100000, 999999)
    otp_store[to_email] = (otp, time.time())
    email_body = EMAIL_BODY_PASSWORD_RESET.format(to_email, otp)

    if await send_smtp_email(to_email, "Your OTP Code", email_body):
        return {"success": True, "message": "OTP sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@app.post("/verify-otp")
async def verify_otp(to_email: str, otp: int):
    if to_email not in otp_store:
        raise HTTPException(status_code=400, detail="OTP not found or expired")

    stored_otp, timestamp = otp_store[to_email]
    if time.time() - timestamp > OTP_EXPIRY_TIME:
        del otp_store[to_email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if stored_otp == otp:
        del otp_store[to_email]
        return {"success": True, "message": "OTP verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
