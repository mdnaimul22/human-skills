from __future__ import annotations
from typing import TypeVar
from .domain import resolve_domain_symbol
from .helpers import (
    Base, BaseStore, SchemaBranch, SchemaMigrator,
    active_tables, discover_branches, load_metadata, system_table_names,
)
from .manager import (
    DatabaseManager, create_tables, ensure_schema_migrations,
    get_db_manager, get_session, init_db, session_scope, shutdown_db,
)
from .system import (
    AuthSession, IdentityRepository, RevokedToken, RevokedTokenRecord,
    RevokedTokenRepository, SessionRepository, User, UserIdentity, UserRepository,
)

T = TypeVar("T")

__all__ = [
    "AuthSession", "Base", "BaseStore", "DatabaseManager",
    "IdentityRepository", "RevokedToken", "RevokedTokenRecord", "RevokedTokenRepository",
    "SchemaBranch", "SchemaMigrator", "SessionRepository", "User", "UserIdentity",
    "UserRepository", "active_tables", "create_tables", "discover_branches",
    "ensure_schema_migrations", "get_db_manager", "get_session", "init_db",
    "load_metadata", "session_scope", "shutdown_db", "system_table_names",
]

def __getattr__(name: str) -> T:
    try:
        return resolve_domain_symbol(name)
    except AttributeError as exc:
        raise AttributeError(f"module 'src.db' has no attribute '{name}'") from exc
