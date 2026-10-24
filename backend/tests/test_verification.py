"""Tests for refund reconciliation against subsequent statements."""
import pytest
from sqlalchemy import select
from backend.app.models.statement import Statement
from backend.app.services.audit_service import audit_service
from backend.app.services.reversal_service import reversal_service
from backend.app.services.verification_service import verification_service


@pytest.mark.asyncio
async def test_subsequent_statement_refund_verification(db_session):
    # 1. Audit Everyday Statement
    stmt = select(Statement).where(Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY")
    res = await db_session.execute(stmt)
    statement = res.scalar_one()
    findings = await audit_service.audit_statement(db_session, statement.id)

    # Pick the $35 overdraft finding
    od_finding = next(f for f in findings if f.fee_amount == 35.0)

    # 2. Draft and approve reversal
    reversal = await reversal_service.draft_reversal(db_session, od_finding.id)
    await reversal_service.record_approval(db_session, reversal.id, "APPROVE", "Senior Auditor")
    await reversal_service.submit_to_mock_bank(db_session, reversal.id)

    # 3. Run verification against subsequent statement
    verification = await verification_service.verify_reversal(db_session, reversal.id)
    assert verification.is_verified is True
    assert verification.verification_status == "MATCHED_EXACT"
    assert verification.verified_amount == 35.0
    assert verification.discrepancy_amount == 0.0
    assert reversal.status == "SETTLED"
