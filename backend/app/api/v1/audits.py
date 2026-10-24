"""Audit execution and findings API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.models.audit import AuditFinding
from backend.app.schemas.audit import AuditFindingResponse, AuditRunSummary
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.post("/run/{statement_id}", response_model=AuditRunSummary)
async def run_audit(statement_id: str, db: AsyncSession = Depends(get_db)):
    """Run fee audit rules on the specified statement."""
    try:
        findings = await audit_service.audit_statement(db, statement_id)
        # Reload with relationships
        stmt = (
            select(AuditFinding)
            .where(AuditFinding.statement_id == statement_id)
            .options(selectinload(AuditFinding.transaction))
        )
        res = await db.execute(stmt)
        all_findings = list(res.scalars().all())

        return AuditRunSummary(
            statement_id=statement_id,
            findings_count=len(all_findings),
            total_fee_amount=sum(f.fee_amount for f in all_findings),
            total_potential_refund=sum(f.potential_refund_amount for f in all_findings),
            findings=all_findings
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/findings", response_model=List[AuditFindingResponse])
async def list_findings(
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    statement_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all audit findings with optional filtering."""
    stmt = select(AuditFinding).options(selectinload(AuditFinding.transaction))
    if status:
        stmt = stmt.where(AuditFinding.status == status.upper())
    if category:
        stmt = stmt.where(AuditFinding.rule_category == category.upper())
    if severity:
        stmt = stmt.where(AuditFinding.severity == severity.upper())
    if statement_id:
        stmt = stmt.where(AuditFinding.statement_id == statement_id)

    stmt = stmt.order_by(AuditFinding.detected_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/findings/{finding_id}", response_model=AuditFindingResponse)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    """Get single audit finding with deep evidence data."""
    stmt = (
        select(AuditFinding)
        .where(AuditFinding.id == finding_id)
        .options(selectinload(AuditFinding.transaction))
    )
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Audit finding not found")
    return finding
