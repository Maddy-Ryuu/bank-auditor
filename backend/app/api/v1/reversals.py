"""Reversal Request, Approval, and Mock Portal Submission endpoints."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.models.reversal import ReversalRequest
from backend.app.models.audit import AuditFinding
from backend.app.schemas.reversal import (
    ReversalRequestResponse,
    ApprovalActionRequest,
    ReversalUpdateRequest,
)
from backend.app.services.reversal_service import reversal_service

router = APIRouter(prefix="/reversals", tags=["Reversals"])


@router.get("", response_model=List[ReversalRequestResponse])
async def list_reversals(
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List reversal requests with status and approval history."""
    stmt = (
        select(ReversalRequest)
        .options(
            selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
            selectinload(ReversalRequest.approvals),
            selectinload(ReversalRequest.mock_ack)
        )
    )
    if status:
        stmt = stmt.where(ReversalRequest.status == status.upper())
    if account_id:
        stmt = stmt.where(ReversalRequest.account_id == account_id)
    stmt = stmt.order_by(ReversalRequest.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/draft/{finding_id}", response_model=ReversalRequestResponse)
async def draft_reversal_request(finding_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and draft a formal fee reversal dispute from an audit finding."""
    try:
        reversal = await reversal_service.draft_reversal(db, finding_id)
        # Reload with relationships
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal.id)
            .options(
                selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{reversal_id}", response_model=ReversalRequestResponse)
async def update_reversal_draft(
    reversal_id: str,
    payload: ReversalUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update a reversal request draft. SAFETY: Invalidates prior approval if approved."""
    try:
        updated = await reversal_service.update_draft(
            db=db,
            reversal_id=reversal_id,
            requested_amount=payload.requested_amount,
            rationale_letter=payload.rationale_letter,
            editor_user=payload.editor_user
        )
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{reversal_id}/action", response_model=ReversalRequestResponse)
async def take_approval_action(
    reversal_id: str,
    payload: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record human approval or rejection before submission to mock portal."""
    try:
        await reversal_service.record_approval(
            db=db,
            reversal_id=reversal_id,
            action=payload.action,
            approved_by_user=payload.approved_by_user,
            notes=payload.notes
        )
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal_id)
            .options(
                selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{reversal_id}/submit-mock-bank")
async def submit_to_mock_bank(reversal_id: str, db: AsyncSession = Depends(get_db)):
    """Submit approved reversal to mock bank portal. Requires prior human approval."""
    try:
        ack_payload = await reversal_service.submit_to_mock_bank(db, reversal_id)
        return {
            "success": True,
            "message": "Dispute successfully acknowledged by Mock Bank Gateway.",
            "acknowledgement": ack_payload
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
