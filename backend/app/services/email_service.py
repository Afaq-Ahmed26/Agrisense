import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def send_device_otp_email(recipient_email: str, device_id: str, otp_code: str, expires_minutes: int) -> None:
    if not (
        settings.SMTP_HOST
        and settings.SMTP_USERNAME
        and settings.SMTP_PASSWORD
        and settings.SMTP_FROM_EMAIL
    ):
        raise RuntimeError("SMTP is not configured for OTP email delivery.")

    subject = "AgriSense Device Connect OTP"
    body = (
        f"Your AgriSense OTP for device {device_id} is: {otp_code}\n\n"
        f"This OTP expires in {expires_minutes} minutes.\n"
        f"If you did not request this, ignore this email."
    )

    message = MIMEMultipart()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, recipient_email, message.as_string())
