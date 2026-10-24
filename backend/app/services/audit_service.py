"""Audit service orchestrating rule evaluations and persisting findings."""
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.statement import Statement, Transaction
from backend.app.models.account import Account, AccountTier
from backend.app.models.tariff import TariffRule
from backend.app.models.audit import AuditFinding
from backend.app.rules.engine import audit_engine
from backend.app.logging_config import logger


class AuditService:
    """Service responsible for executing audits on statements and saving findings."""

    async def audit_statement(self, db: AsyncSession, statement_id: str) -> List[AuditFinding]:
        """Run audit rules engine on the given statement and persist findings."""
        # Load statement with account, tier, and transactions
        stmt = (
            select(Statement)
            .where(Statement.id == statement_id)
            .options(
                selectinload(Statement.account).selectinload(Account.tier),
                selectinload(Statement.transactions),
                selectinload(Statement.findings)
            )
        )
        result = await db.execute(stmt)
        statement = result.scalar_one_or_none()
        if not statement:
            raise ValueError(f"Statement with ID {statement_id} not found.")

        account = statement.account
        tier = account.tier if account else None

        # Fetch applicable tariff rules for this tier
        tariff_rules: List[TariffRule] = []
        if tier:
            t_stmt = select(TariffRule).where(TariffRule.tier_id == tier.id)
            t_res = await db.execute(t_stmt)
            tariff_rules = list(t_res.scalars().all())

        # Evaluate rules
        eval_findings = audit_engine.run_audit(
            statement=statement,
            account=account,
            tier=tier,
            tariff_rules=tariff_rules,
            transactions=statement.transactions
        )

        persisted_findings: List[AuditFinding] = []

        # Delete previously flagged findings for this statement if re-auditing
        existing_stmt = select(AuditFinding).where(AuditFinding.statement_id == statement_id)
        existing_res = await db.execute(existing_stmt)
        for old in existing_res.scalars().all():
            if old.status == "FLAGGED":
                await db.delete(old)
        await db.flush()

        for ef in eval_findings:
            finding = AuditFinding(
                statement_id=statement.id,
                transaction_id=ef.transaction_id,
                rule_id=ef.rule_id,
                rule_category=ef.rule_category,
                fee_amount=ef.fee_amount,
                potential_refund_amount=ef.potential_refund_amount,
                severity=ef.severity,
                status="FLAGGED",
                violation_title=ef.violation_title,
                violation_reason=ef.violation_reason,
                evidence_data=ef.evidence_data,
                source_evidence_snapshot=ef.source_evidence_snapshot,
            )
            db.add(finding)
            persisted_findings.append(finding)

        await db.commit()
        for f in persisted_findings:
            await db.refresh(f)

        logger.info(
            f"Successfully audited statement {statement_id}. "
            f"Generated {len(persisted_findings)} audit findings."
        )
        return persisted_findings


audit_service = AuditService()
