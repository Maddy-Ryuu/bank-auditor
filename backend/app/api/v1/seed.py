"""Seed data and test run execution API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db, init_db
from backend.app.config import settings
from backend.app.seed_data import seed_database
from backend.app.services.test_runner import test_runner_service
from backend.app.schemas.test_run import TestRunResponse

router = APIRouter(prefix="/seed", tags=["Seed & Test Runs"])


@router.post("/reset")
async def reset_seed_data(db: AsyncSession = Depends(get_db)):
    """Initialize schema and reload standard synthetic datasets (Development/Test only)."""
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=403,
            detail="Automated database reset is strictly prohibited in production environments."
        )
    await init_db()
    await seed_database(db, run_initial_audit=True)
    return {"message": "Synthetic database successfully seeded with baseline scenarios and audit run."}


@router.post("/run-audit-suite", response_model=TestRunResponse)
async def run_audit_suite(db: AsyncSession = Depends(get_db)):
    """Execute end-to-end audit scenario test run across all seeded statements."""
    test_run = await test_runner_service.run_synthetic_audit_suite(db)
    return test_run
