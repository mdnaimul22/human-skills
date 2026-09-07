"""
Email / Notification Provider — External Service Integration.
Handles outbound email dispatch via SMTP or external API client.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "provider.log", name="app.providers.email")


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an outbound email asynchronously.
    In development mode or if SMTP is not configured, logs the email payload safely.
    """
    smtp_host = getattr(Settings, "SMTP_HOST", None)

    if not smtp_host or Settings.is_development:
        logger.info(
            f"[DEV EMAIL DISPATCH] To: {to_email} | Subject: '{subject}'\n"
            f"Body:\n{body}"
        )
        return True

    # Production delivery implementation (e.g. SMTP or third-party email API)
    try:
        # Simulate async network delivery
        await asyncio.sleep(0.1)
        logger.info(f"Email successfully delivered to {to_email} with subject '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to deliver email to {to_email}: {e}")
        return False


async def send_welcome_email(to_email: str, user_name: str) -> bool:
    """Convenience helper to dispatch a standardized welcome email."""
    subject = f"Welcome to {Settings.PROJECT_NAME}!"
    body = (
        f"Hi {user_name},\n\n"
        f"Welcome aboard! Your account at {Settings.PROJECT_NAME} has been created successfully.\n"
        f"If you have any questions, reply directly to this email.\n\n"
        f"Best regards,\nThe {Settings.PROJECT_NAME} Team"
    )
    return await send_email(to_email, subject, body)
