"""Tests for reversal lifecycle: draft, approval gating, and mock bank submission."""
import pytest
from sqlalchemy import select
from backend.app.models.statement import Statement
from backend.app.services.audit_service import audit_service
from backend.app.services.reversal_service import reversal_service


@pytest.mark.asyncio
async def test_reversal_lifecycle_and_approval_gating(db_session):
    # 1. Audit a statement
    stmt = select(Statement).where(Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY")
    res = await db_session.execute(stmt)
    statement = res.scalar_one()
    findings = await audit_service.audit_statement(db_session, statement.id)
    finding = findings[0]

    # 2. Draft reversal
    reversal = await reversal_service.draft_reversal(db_session, finding.id, prepared_by="Test Suite Engine")
    assert reversal.status == "PENDING_APPROVAL"
    assert "DISPUTE NOTICE" in reversal.rationale_letter
    assert reversal.requested_amount == finding.potential_refund_amount

    # 3. GATING CHECK: Submitting unapproved reversal MUST raise ValueError!
    with pytest.raises(ValueError) as excinfo:
        await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert "Explicit human approval is required prior to submission" in str(excinfo.value)

    # 4. Human Approval
    approved_reversal = await reversal_service.record_approval(
        db=db_session,
        reversal_id=reversal.id,
        action="APPROVE",
        approved_by_user="Jane Doe (Lead Auditor)",
        notes="Verified average daily balance evidence. Proceed with mock submission."
    )
    assert approved_reversal.status == "APPROVED"
    assert len(approved_reversal.approvals) == 1
    assert approved_reversal.approvals[0].approved_by_user == "Jane Doe (Lead Auditor)"

    # 5. Submission to Mock Bank Portal
    ack = await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert ack["status"] == "ACCEPTED"
    assert "MB-TKT-" in ack["ticket_id"]
    assert approved_reversal.status == "ACKNOWLEDGED"
