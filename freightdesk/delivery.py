"""Email delivery: real SMTP when configured, explicit mock otherwise."""

import os
import smtplib
from email.message import EmailMessage

from .models import Draft


def smtp_config() -> dict | None:
    host = os.getenv("FREIGHTDESK_SMTP_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("FREIGHTDESK_SMTP_PORT", "587")),
        "user": os.getenv("FREIGHTDESK_SMTP_USER", ""),
        "password": os.getenv("FREIGHTDESK_SMTP_PASSWORD", ""),
        "sender": os.getenv("FREIGHTDESK_SMTP_FROM", "freightdesk@localhost"),
    }


def deliver(draft: Draft, cc: list[str] | None = None) -> tuple[str, str]:
    """Send the approved draft. Returns (mode, detail):
    mode 'smtp' on real delivery, 'mock' when SMTP is unconfigured or the
    customer has no address on file. Never raises past this boundary."""
    config = smtp_config()
    if not draft.email_to:
        return "mock", "no recipient on file for this customer"
    if config is None:
        return "mock", "SMTP not configured (set FREIGHTDESK_SMTP_HOST to enable)"

    message = EmailMessage()
    message["Subject"] = draft.email_subject
    message["From"] = config["sender"]
    message["To"] = draft.email_to
    if cc:
        message["Cc"] = ", ".join(cc)
    message.set_content(draft.email_body)

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as server:
            if config["user"]:
                server.starttls()
                server.login(config["user"], config["password"])
            server.send_message(message)
        return "smtp", f"delivered to {draft.email_to}"
    except (smtplib.SMTPException, OSError) as error:
        return "mock", f"SMTP failed ({error}); recorded without delivery"
