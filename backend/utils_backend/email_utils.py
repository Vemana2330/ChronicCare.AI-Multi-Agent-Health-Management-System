# backend/utils/email_utils.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")     # your gmail address
EMAIL_PASS = os.getenv("EMAIL_PASS")     # app password

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email
    msg["Subject"] = subject

    # ✅ Specify UTF-8 encoding explicitly here
    msg.attach(MIMEText(body, "html", _charset="utf-8"))


    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

