from __future__ import annotations

import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


def _send_email(receiver_email: str, subject: str, body: str) -> None:
    """
    Send an email to the specified email address.
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, receiver_email, msg.as_string())
        return True

    except Exception as e:
        return False
    finally:
        server.quit()


async def send_email(receiver_email: str, subject: str, body: str) -> bool:
    """
    Send an email to the specified email address.
    """
    return await asyncio.get_event_loop().run_in_executor(
        None, _send_email, receiver_email, subject, body
    )
