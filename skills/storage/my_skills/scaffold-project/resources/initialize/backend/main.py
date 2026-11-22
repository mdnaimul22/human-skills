from contextlib import asynccontextmanager
import asyncio
import os
import subprocess
import sys

import uvicorn
from fastapi import FastAPI

from src.config import Settings, setup_logger, shutdown_logger, uvicorn_logging
from src.helpers import (
    register_cors,
    register_middleware,
    register_error_handlers,
    kill_pid,
    init_redis,
    shutdown_redis,
)
from src.apps import (
    DockerManager,
    NginxManager,
    WAFManager,
    get_git_manager,
    get_manager,
    get_system_manager,
)
from src.services.intelligence import populate_missing_metadata
from src.services.history_service import persist_file_record
from src.core import ClashManager, EgressManager, get_egress_manager
from src.db import DatabaseManager
from src.routers import tools_router, auth_router, workspace_router, statistics_router, system_router

logger = setup_logger(
    Settings.LOG_DIR / "main.log",
    name="Vidula.main",
)
db_manager = DatabaseManager()


async def _startup_apps() -> None:
    db_manager.initialize(Settings.DATABASE_URL)
    await db_manager.create_tables()
    await db_manager.migrate()
    logger.info("Database initialized & schema migrated")

    try:
        docker_results = DockerManager().ensure_all()
        for name, ok in docker_results.items():
            if not ok:
                logger.warning(f"Docker container '{name}' failed to reach active state.")
    except Exception as e:
        logger.error(f"DockerManager execution failed: {e}")

    try:
        await init_redis()
    except Exception as e:
        logger.warning(f"Failed to initialize Redis cache: {e}")

    sys_mgr = get_system_manager()
    await sys_mgr.start_async()

    manager = get_manager()
    await manager.start()

    try:
        if NginxManager.setup_and_reload():
            logger.info("Nginx automated setup and reload succeeded.")
        else:
            logger.warning("Nginx automated setup failed.")
    except Exception as e:
        logger.error(f"Failed to run Nginx manager on startup: {e}")

    WAFManager().start_flush_task()

    try:
        git_results = get_git_manager().start_all()
        logger.info(f"GitManager autonomous workers started: {git_results}")
    except Exception as e:
        logger.error(f"Failed to start GitManager on startup: {e}")


async def _shutdown_apps() -> None:
    try:
        await asyncio.to_thread(get_git_manager().stop_all)
        logger.info("GitManager workers stopped cleanly.")
    except Exception as e:
        logger.error(f"Failed to stop GitManager on shutdown: {e}")

    await WAFManager().shutdown()
    await get_manager().shutdown()
    await get_system_manager().stop_async()
    await shutdown_redis()
    await db_manager.shutdown()


async def _startup_domain() -> None:
    get_manager().results.set_completion_callback(persist_file_record)

    try:
        DockerManager().ensure_container_running()
        from src.helpers.po_token import get_po_token_pool
        get_po_token_pool().start()
    except Exception as e:
        logger.warning(f"Failed to initialize Docker sidecar manager or PO token pool: {e}")

    asyncio.create_task(populate_missing_metadata())

    try:
        await ClashManager().start()
        logger.info("Clash/Mihomo proxy daemon started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Clash daemon on startup: {e}")

    try:
        egress_mgr = get_egress_manager()
        egress_mgr.start()
        logger.info("EgressManager initialized and health checker started successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize EgressManager on startup: {e}")


async def _shutdown_domain() -> None:
    try:
        from src.helpers.po_token import get_po_token_pool
        await get_po_token_pool().stop()
    except Exception as e:
        logger.debug(f"PO Token Pool shutdown error: {e}")

    try:
        get_egress_manager().stop()
    except Exception as e:
        logger.error(f"Failed to stop EgressManager on shutdown: {e}")

    try:
        await ClashManager().stop()
        logger.info("Clash/Mihomo proxy daemon stopped cleanly.")
    except Exception as e:
        logger.error(f"Failed to stop Clash daemon on shutdown: {e}")

    try:
        DockerManager().stop_container("movie-pot-provider")
    except Exception as e:
        logger.debug(f"Docker sidecar stop bypassed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    uvicorn_logging()
    await _startup_apps()
    await _startup_domain()
    logger.info(f"🚀 {Settings.PROJECT_NAME} v{Settings.VERSION} started in {Settings.ENV} mode")
    yield
    logger.info("Shutting down application...")
    await _shutdown_domain()
    await _shutdown_apps()
    shutdown_logger()


app = FastAPI(
    title=Settings.PROJECT_NAME,
    version=Settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not Settings.is_production else None,
    redoc_url=None,
)

register_cors(app, Settings)
register_middleware(app, logger, Settings)
register_error_handlers(app, logger)

app.include_router(system_router)
app.include_router(tools_router)
app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(statistics_router)


if __name__ == "__main__":
    kill_pid(Settings.API_PORT)
    uvicorn.run(
        "main:app",
        host=Settings.API_HOST,
        port=Settings.API_PORT,
        reload=False,
        log_config=uvicorn.config.LOGGING_CONFIG,
    )
