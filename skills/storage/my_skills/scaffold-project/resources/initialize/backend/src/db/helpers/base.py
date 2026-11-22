from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from src.helpers import get_now_utc

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

def uuid_hex() -> str:
    return uuid.uuid4().hex

def utc_now() -> datetime:
    return get_now_utc()
