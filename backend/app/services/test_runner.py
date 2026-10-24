"""Automated test scenario runner for audit benchmarking and validation."""
import time
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.statement import Statement
from backend.app.models.test_run import TestRun
from backend.app.services.audit_service import audit_service
from backend.app.logging_config import logger


class TestRunnerService:
    """Runs automated synthetic audit test suites."""

    async def run_synthetic_audit_suite(self, db: AsyncSession, test_suite_name: str = "Synthetic Statements Baseline Audit") -> TestRun:
        """Runs audit engine across all primary initial statements and logs performance metrics."""
        start_time = time.perf_counter()

        stmt = select(Statement).where(Statement.is_subsequent_statement.is_(False))
        result = await db.execute(stmt)
        statements = list(result.scalars().all())

        total_findings = 0
        total_recovery = 0.0
        total_fee_audited = 0.0
        details: Dict[str, Any] = {"statements_tested": []}

        for st in statements:
            findings = await audit_service.audit_statement(db, st.id)
            stmt_fee = sum(f.fee_amount for f in findings)
            stmt_recovery = sum(f.potential_refund_amount for f in findings)
            total_findings += len(findings)
            total_recovery += stmt_recovery
            total_fee_audited += stmt_fee

            details["statements_tested"].append({
                "statement_id": st.id,
                "source_id": st.source_id,
                "findings_count": len(findings),
                "potential_recovery": stmt_recovery,
                "categories": list(set(f.rule_category for f in findings))
            })

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        test_run = TestRun(
            test_suite_name=test_suite_name,
            run_type="SYNTHETIC_E2E_AUDIT",
            status="SUCCESS",
            findings_detected_count=total_findings,
            total_fee_amount_audited=total_fee_audited,
            potential_recovery_amount=total_recovery,
            execution_duration_ms=duration_ms,
            details=details,
            executed_at=datetime.now(timezone.utc)
        )
        db.add(test_run)
        await db.commit()
        await db.refresh(test_run)

        logger.info(
            f"Completed test run '{test_suite_name}' in {duration_ms}ms: "
            f"{total_findings} findings detected, ${total_recovery:.2f} potential recovery."
        )
        return test_run


test_runner_service = TestRunnerService()
