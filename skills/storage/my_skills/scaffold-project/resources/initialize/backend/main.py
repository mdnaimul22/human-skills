from contextlib import asynccontextmanager
import asyncio

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
    get_job_manager,
    get_system_manager,
    get_tunnel_manager,
)
from src.db import DatabaseManager
from src.routers import auth_router, system_router

logger = setup_logger(boss_name="main.txt")
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

    job_mgr = get_job_manager()
    await job_mgr.start()

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

    try:
        await get_tunnel_manager().start_async()
    except Exception as e:
        logger.error(f"Failed to start TunnelManager on startup: {e}")


async def _shutdown_apps() -> None:
    try:
        await get_tunnel_manager().stop_async()
    except Exception as e:
        logger.error(f"Failed to stop TunnelManager on shutdown: {e}")

    try:
        await asyncio.to_thread(get_git_manager().stop_all)
        logger.info("GitManager workers stopped cleanly.")
    except Exception as e:
        logger.error(f"Failed to stop GitManager on shutdown: {e}")

    await WAFManager().shutdown()
    await get_job_manager().shutdown()
    await get_system_manager().stop_async()
    await shutdown_redis()
    await db_manager.shutdown()


async def _startup_domain() -> None:
    pass


async def _shutdown_domain() -> None:
    pass


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
app.include_router(auth_router)


if __name__ == "__main__":
    kill_pid(Settings.API_PORT)
    uvicorn.run(
        "main:app",
        host=Settings.API_HOST,
        port=Settings.API_PORT,
        reload=False,
        log_config=uvicorn.config.LOGGING_CONFIG,
    )
