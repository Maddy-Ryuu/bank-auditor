"""Main FastAPI application entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.app.config import settings
from backend.app.logging_config import setup_logging, logger
from backend.app.database import init_db, AsyncSessionLocal
from backend.app.seed_data import seed_database
from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.health import router as root_health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for initialization and teardown."""
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")

    # Initialize tables
    await init_db()

    # Seed baseline synthetic data only in non-production environments if empty
    async with AsyncSessionLocal() as session:
        try:
            if settings.APP_ENV != "production":
                await seed_database(session, run_initial_audit=True)
            else:
                logger.info("Production environment: automatic database seeding is disabled.")
        except Exception as exc:
            logger.error(f"Error checking initial database state: {exc}", exc_info=True)

    logger.info("Application startup completed successfully.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Bank Fee Audit, Human Approval, Mock Portal Submission & Verification Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global API routers
app.include_router(root_health_router, prefix="/api")
app.include_router(api_v1_router, prefix="/api")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error_type": type(exc).__name__}
    )


# Static frontend files mounting for Render production deployment
FRONTEND_DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow /api and /docs routes to pass through
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        file_path = os.path.join(FRONTEND_DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST_DIR, "index.html"))
else:
    @app.get("/")
    async def fallback_root():
        return {
            "app_name": settings.APP_NAME,
            "status": "online",
            "message": "Backend API operational. Build frontend assets to enable web dashboard.",
            "docs": "/docs"
        }
