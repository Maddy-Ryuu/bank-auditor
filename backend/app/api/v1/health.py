"""Health check endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check verifying database connection and service configuration."""
    db_status = "ok"
    status_code = 200
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {type(exc).__name__}"
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "online" if db_status == "ok" else "degraded",
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock_bank_gateway": settings.MOCK_BANK_PORTAL_NAME,
            "version": "1.0.0"
        }
    )
