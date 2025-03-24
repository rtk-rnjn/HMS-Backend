import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]


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
