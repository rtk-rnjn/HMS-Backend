from __future__ import annotations

import os
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


async def send_email(receiver_email: str, subject: str, body: str) -> bool:
    """
    Send an email asynchronously to the specified email address.
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT)
        await server.connect()
        await server.starttls()
        await server.login(EMAIL, PASSWORD)
        await server.send_message(msg)
        await server.quit()
        return True
    except Exception:
        return False
