from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from src.config import Settings, setup_logger, PROJECT_ROOT
from src.helpers import (
    register_cors,
    register_middleware,
    register_error_handlers,
    init_db,
    shutdown_db,
    kill_process_on_port
)

# 1. Initialize Logger
logger = setup_logger(
    PROJECT_ROOT / "logs" / "app.log", 
    name="app.main"
)

# 2. Define Lifespan (Startup/Shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info(f"Starting {Settings.PROJECT_NAME} in {Settings.ENV} mode...")
    
    # Initialize Database (Uncomment if using a database)
    # db_url = getattr(Settings, "DATABASE_URL", "sqlite+aiosqlite:///data/db.sqlite3")
    # await init_db(db_url, echo=not Settings.is_production)
    
    yield
    
    # --- Shutdown ---
    logger.info("Shutting down application...")
    # await shutdown_db()

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
# from src.routers.user import router as user_router
# app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])

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
    
    # Ensure port is free before starting
    kill_process_on_port(port)
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=not Settings.is_production
    )
