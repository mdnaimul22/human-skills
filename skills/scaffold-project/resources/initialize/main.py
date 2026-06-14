from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from src.config import Settings, setup_logger, shutdown_logger, PROJECT_ROOT
from src.helpers import (
    register_cors,
    register_middleware,
    register_error_handlers,
    init_db,
    shutdown_db,
    kill_pid,
    connection
)
from src.db.models import Base
from src.routers.auth import router as auth_router

# 1. Initialize Logger
logger = setup_logger(
    PROJECT_ROOT / "logs" / "app.log", 
    name="app.main"
)

# 2. Define Lifespan (Startup/Shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database
    init_db(Settings.DATABASE_URL)
    async with connection._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    
    yield
    
    # --- Shutdown ---
    logger.info("Shutting down application...")
    await shutdown_db()
    shutdown_logger()

# 3. Initialize FastAPI App
app = FastAPI(
    title=Settings.PROJECT_NAME,
    version=Settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not Settings.is_production else None,
    redoc_url=None
)

# 4. Register Infrastructure / Helpers
register_cors(app, Settings)
register_middleware(app, logger, Settings)
register_error_handlers(app, logger)

# 5. Include Routers
app.include_router(auth_router)

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok", 
        "project": Settings.PROJECT_NAME,
        "environment": Settings.ENV,
        "version": Settings.VERSION
    }

if __name__ == "__main__":
    # Fallback host and port if not defined in Settings
    host = getattr(Settings, "API_HOST", "127.0.0.1")
    port = getattr(Settings, "API_PORT", 8000)
    
    # ⚠️ DO NOT REMOVE — Auto-kills any orphaned server process holding this port.
    # Without this, you'll get "Address already in use" errors on restart.
    kill_pid(port)
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=not Settings.is_production
    )
