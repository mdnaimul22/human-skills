from __future__ import annotations

import asyncio

from src.config import Settings, setup_logger
from src.schema import GoogleUserInfo
from src.helpers import AuthenticationError, ValidationError

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

logger = setup_logger(boss_name="providers.main.txt", his_name="providers.google.txt")


async def verify_google_token(token: str) -> GoogleUserInfo:
    if not Settings.GOOGLE_CLIENT_ID:
        raise ValidationError("Google OAuth is not configured: set GOOGLE_CLIENT_ID in .env")

    try:
        payload = await asyncio.to_thread(
            google_id_token.verify_oauth2_token,
            token,
            google_requests.Request(),
            Settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise AuthenticationError("Invalid Google token")

    email = payload.get("email")
    if not email:
        raise AuthenticationError("Google token missing email claim")

    return GoogleUserInfo(
        google_id=payload["sub"],
        email=email.lower(),
        name=payload.get("name", ""),
        email_verified=payload.get("email_verified", False),
    )
