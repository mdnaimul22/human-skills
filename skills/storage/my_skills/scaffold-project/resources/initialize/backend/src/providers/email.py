from __future__ import annotations

from email.message import EmailMessage

from src.config import Settings, setup_logger

logger = setup_logger(boss_name="providers.main.txt", his_name="providers.email.txt")


async def _send_smtp(msg: EmailMessage) -> bool:
    import aiosmtplib

    await aiosmtplib.send(
        msg,
        hostname=Settings.SMTP_HOST,
        port=Settings.SMTP_PORT,
        username=Settings.SMTP_USER,
        password=Settings.SMTP_PASSWORD,
        start_tls=True,
    )
    return True


def _build_message(to_email: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = Settings.SMTP_FROM_EMAIL or f"noreply@{Settings.PROJECT_NAME.lower()}.com"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


async def send_email(to_email: str, subject: str, body: str) -> bool:
    if not Settings.SMTP_HOST or Settings.is_development:
        logger.info(
            f"[DEV EMAIL] To: {to_email} | Subject: '{subject}'\n"
            f"Body:\n{body}"
        )
        return True

    try:
        msg = _build_message(to_email, subject, body)
        await _send_smtp(msg)
        logger.info(f"Email delivered to {to_email}: '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to deliver email to {to_email}: {e}")
        return False


async def send_welcome_email(to_email: str, user_name: str) -> bool:
    subject = f"Welcome to {Settings.PROJECT_NAME}!"
    body = (
        f"Hi {user_name},\n\n"
        f"Welcome aboard! Your account at {Settings.PROJECT_NAME} has been created successfully.\n"
        f"If you have any questions, reply directly to this email.\n\n"
        f"Best regards,\nThe {Settings.PROJECT_NAME} Team"
    )
    return await send_email(to_email, subject, body)


async def _send_action_email(
    to_email: str,
    user_name: str,
    subject: str,
    action_text: str,
    action_url: str,
    expiry_hours: int,
    ignore_text: str,
) -> bool:
    body = (
        f"Hi {user_name},\n\n"
        f"{action_text}:\n\n"
        f"{action_url}\n\n"
        f"This link expires in {expiry_hours} hour(s).\n"
        f"{ignore_text}\n\n"
        f"Best regards,\nThe {Settings.PROJECT_NAME} Team"
    )
    return await send_email(to_email, subject, body)


async def send_verification_email(to_email: str, user_name: str, token: str) -> bool:
    return await _send_action_email(
        to_email=to_email,
        user_name=user_name,
        subject=f"Verify your email — {Settings.PROJECT_NAME}",
        action_text="Please verify your email address by clicking the link below",
        action_url=f"{Settings.FRONTEND_VERIFY_URL}?token={token}",
        expiry_hours=Settings.VERIFY_TOKEN_EXPIRY_HOURS,
        ignore_text="If you didn't create this account, ignore this email.",
    )


async def send_password_reset_email(to_email: str, user_name: str, token: str) -> bool:
    return await _send_action_email(
        to_email=to_email,
        user_name=user_name,
        subject=f"Reset your password — {Settings.PROJECT_NAME}",
        action_text="We received a request to reset your password. Click the link below",
        action_url=f"{Settings.FRONTEND_RESET_URL}?token={token}",
        expiry_hours=Settings.RESET_TOKEN_EXPIRY_HOURS,
        ignore_text="If you didn't request this, ignore this email.",
    )
