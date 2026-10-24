"""Tests for statement auditing workflow."""
import pytest
from sqlalchemy import select
from backend.app.models.statement import Statement
from backend.app.models.audit import AuditFinding
from backend.app.services.audit_service import audit_service


@pytest.mark.asyncio
async def test_audit_seeded_everyday_statement(db_session):
    # Find the Everyday Checking initial statement
    stmt = (
        select(Statement)
        .where(
            Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
            Statement.is_subsequent_statement.is_(False)
        )
    )
    res = await db_session.execute(stmt)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    assert len(findings) >= 3

    categories = {f.rule_category for f in findings}
    assert "MONTHLY_MAINTENANCE" in categories
    assert "OVERDRAFT" in categories
    assert "PAPER_STATEMENT" in categories

    total_recovery = sum(f.potential_refund_amount for f in findings)
    assert total_recovery >= 50.0  # $12 + $35 + $3 = $50


@pytest.mark.asyncio
async def test_audit_premier_statement(db_session):
    stmt = select(Statement).where(Statement.source_id == "SYNTH-STMT-2024-03-PREMIER")
    res = await db_session.execute(stmt)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    assert len(findings) >= 2
    categories = {f.rule_category for f in findings}
    assert "WIRE_TRANSFER" in categories
    assert "FOREIGN_TRANSACTION" in categories
