"""Refund Verification API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.verification import VerificationResult
from backend.app.schemas.verification import (
    VerificationResultResponse,
    VerificationRunRequest,
)
from backend.app.services.verification_service import verification_service

router = APIRouter(prefix="/verifications", tags=["Verifications"])


@router.get("", response_model=List[VerificationResultResponse])
async def list_verifications(
    status: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List refund verification reconciliation results."""
    stmt = select(VerificationResult)
    if status:
        stmt = stmt.where(VerificationResult.verification_status == status.upper())
    if is_verified is not None:
        stmt = stmt.where(VerificationResult.is_verified == is_verified)
    stmt = stmt.order_by(VerificationResult.verified_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/verify", response_model=VerificationResultResponse)
async def run_verification(
    payload: VerificationRunRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reconcile reversal refund against subsequent statement."""
    try:
        verification = await verification_service.verify_reversal(
            db=db,
            reversal_id=payload.reversal_id,
            subsequent_statement_id=payload.subsequent_statement_id
        )
        return verification
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
