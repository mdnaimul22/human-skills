from __future__ import annotations
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from src.config import Settings

def _build_fernet(secret: str | None = None) -> Fernet:
    raw = (secret or Settings.JWT_SECRET).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt_secret(plaintext: str | None) -> str | None:
    if not plaintext:
        return None
    fernet = _build_fernet()
    try:
        fernet.decrypt(plaintext.encode("utf-8"))
        return plaintext
    except (InvalidToken, ValueError):
        return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return None
    fernet = _build_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
