from __future__ import annotations
import re
import uuid
from typing import Protocol, cast
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from src.config import Settings, setup_logger
from src.db.helpers.base import Base
from src.db.helpers.registry import active_tables, system_table_names
from src.helpers import ValidationError

logger = setup_logger(Settings.LOG_DIR / "db.log", name="db.migrations")
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
_INTERNAL_TABLES = {"sqlite_sequence", "alembic_version"}

class InspectorProtocol(Protocol):
    def has_table(self, table_name: str) -> bool: ...
    def get_table_names(self) -> list[str]: ...
    def get_columns(self, table_name: str) -> list[dict[str, str]]: ...

class SchemaMigrator:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.last_orphans: list[str] = []

    def _get_existing_columns(self, sync_conn: Connection, table_name: str) -> set[str]:
        insp = cast(InspectorProtocol, inspect(sync_conn))
        if not insp.has_table(table_name):
            return set()
        return {col["name"] for col in insp.get_columns(table_name)}

    def _get_existing_tables(self, sync_conn: Connection) -> set[str]:
        insp = cast(InspectorProtocol, inspect(sync_conn))
        return set(insp.get_table_names())

    def _resolve_default_clause(self, table: Table, col_name: str) -> str:
        col = table.columns[col_name]
        if col.server_default is not None:
            return str(col.server_default.arg)
        if col.default is not None and col.default.is_scalar:
            val = col.default.arg
            if type(val) is str:
                return f"'{val}'"
            return str(val)
        return ""

    def _build_alter_sql(
        self, table_name: str, col_name: str, col_type: str, default_clause: str,
    ) -> str:
        if not _IDENTIFIER_PATTERN.match(table_name) or not _IDENTIFIER_PATTERN.match(col_name):
            raise ValidationError(f"Invalid identifier: {table_name}.{col_name}")
        tokens = ["ALTER", "TABLE", f'"{table_name}"', "ADD", "COLUMN", f'"{col_name}"', col_type]
        if default_clause:
            tokens.extend(["DEFAULT", default_clause])
        return " ".join(tokens)

    def _build_drop_sql(self, table_name: str) -> str:
        if not _IDENTIFIER_PATTERN.match(table_name):
            raise ValidationError(f"Invalid table identifier: {table_name}")
        tokens = ["DROP", "TABLE", "IF", "EXISTS", f'"{table_name}"']
        return " ".join(tokens)

    async def migrate_table(self, conn: AsyncConnection, table: Table) -> list[str]:
        applied: list[str] = []
        table_name = table.name
        existing_cols = await conn.run_sync(self._get_existing_columns, table_name)
        if not existing_cols:
            return applied
        dialect = conn.dialect
        for col in table.columns:
            if col.name in existing_cols:
                continue
            col_type = col.type.compile(dialect)
            default_clause = self._resolve_default_clause(table, col.name)
            sql = self._build_alter_sql(table_name, col.name, col_type, default_clause)
            await conn.exec_driver_sql(sql)
            applied.append(f"{table_name}.{col.name}")
            logger.info(f"Schema migration applied: {table_name}.{col.name} ({col_type})")
        return applied

    async def _migrate_legacy_users(self, conn: AsyncConnection) -> list[str]:
        existing_cols = await conn.run_sync(self._get_existing_columns, "users")
        if "google_id" not in existing_cols:
            return []
        has_oauth_cols = {"access_token", "refresh_token", "token_expires_at"}.issubset(existing_cols)
        if has_oauth_cols:
            res = await conn.exec_driver_sql(
                "SELECT id, google_id, access_token, refresh_token, token_expires_at, created_at, updated_at FROM users"
            )
        else:
            res = await conn.exec_driver_sql(
                "SELECT id, google_id, NULL, NULL, NULL, created_at, updated_at FROM users"
            )
        rows = res.fetchall()
        for row in rows:
            uid, gid, atok, rtok, exp, c_at, u_at = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            if not gid:
                continue
            await conn.exec_driver_sql(
                "INSERT OR IGNORE INTO user_identities "
                "(id, user_id, provider, subject, access_token_enc, refresh_token_enc, token_expires_at, created_at, updated_at) "
                "VALUES (:id, :uid, 'google', :sub, :at, :rt, :exp, COALESCE(:ca, CURRENT_TIMESTAMP), COALESCE(:ua, CURRENT_TIMESTAMP))",
                {"id": uuid.uuid4().hex, "uid": uid, "sub": gid, "at": atok, "rt": rtok, "exp": exp, "ca": c_at, "ua": u_at},
            )
        await conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        await conn.exec_driver_sql("DROP TABLE IF EXISTS users__new")
        await conn.exec_driver_sql(
            "CREATE TABLE users__new ("
            "id VARCHAR(32) NOT NULL, email VARCHAR(255) NOT NULL, name VARCHAR(100) NOT NULL, "
            "avatar_url TEXT, tier VARCHAR(20) DEFAULT 'registered' NOT NULL, "
            "status VARCHAR(20) DEFAULT 'active' NOT NULL, "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, "
            "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, "
            "CONSTRAINT pk_users PRIMARY KEY (id))"
        )
        has_profile_cols = {"avatar_url", "tier"}.issubset(existing_cols)
        if has_profile_cols:
            await conn.exec_driver_sql(
                "INSERT INTO users__new (id, email, name, avatar_url, tier, status, created_at, updated_at) "
                "SELECT id, email, name, avatar_url, COALESCE(tier, 'registered'), 'active', "
                "COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP) FROM users"
            )
        else:
            await conn.exec_driver_sql(
                "INSERT INTO users__new (id, email, name, avatar_url, tier, status, created_at, updated_at) "
                "SELECT id, email, name, NULL, 'registered', 'active', "
                "COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP) FROM users"
            )
        await conn.exec_driver_sql("DROP TABLE users")
        await conn.exec_driver_sql("ALTER TABLE users__new RENAME TO users")
        await conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        logger.info("Migrated legacy users.google_id and OAuth tokens into user_identities")
        return ["users.identities_migrated", "users.schema_normalized"]

    async def detect_orphans(self, conn: AsyncConnection, active_names: set[str]) -> list[str]:
        existing = await conn.run_sync(self._get_existing_tables)
        sys_names = system_table_names()
        orphans = sorted(existing - active_names - sys_names - _INTERNAL_TABLES)
        self.last_orphans = orphans
        if orphans:
            logger.warning(f"Orphan domain tables detected (domain removed from disk): {orphans}")
        return orphans

    async def prune_orphans(self, domain_root: str = "src/db/domain") -> list[str]:
        tables = active_tables(domain_root)
        active_names = {t.name for t in tables}
        dropped: list[str] = []
        async with self.engine.begin() as conn:
            orphans = await self.detect_orphans(conn, active_names)
            for table_name in orphans:
                sql = self._build_drop_sql(table_name)
                await conn.exec_driver_sql(sql)
                dropped.append(table_name)
                logger.info(f"Pruned orphan domain table: {table_name}")
            self.last_orphans = []
        return dropped

    async def run(
        self, metadata: MetaData | None = None, domain_root: str = "src/db/domain",
    ) -> dict[str, list[str]]:
        results: dict[str, list[str]] = {}
        custom_meta = metadata is not None and metadata is not Base.metadata
        async with self.engine.begin() as conn:
            if custom_meta and metadata is not None:
                for table_name, table in metadata.tables.items():
                    applied = await self.migrate_table(conn, table)
                    if applied:
                        results[table_name] = applied
                return results
            tables = active_tables(domain_root)
            existing_before = await conn.run_sync(self._get_existing_tables)
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
            for table in tables:
                if table.name not in existing_before:
                    results[table.name] = [f"{table.name}.__created__"]
            legacy_applied = await self._migrate_legacy_users(conn)
            if legacy_applied:
                results.setdefault("users", []).extend(legacy_applied)
            for table in tables:
                applied = await self.migrate_table(conn, table)
                if applied:
                    results.setdefault(table.name, []).extend(applied)
            await self.detect_orphans(conn, {t.name for t in tables})
        return results
