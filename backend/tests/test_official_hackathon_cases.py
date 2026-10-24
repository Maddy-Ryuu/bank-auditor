"""Official Ziro Hackathon Test Cases and Safety Checklist Suite.

Covers:
- TC1: Wrong minimum-balance fee
- TC2: Tariff of a different account tier
- TC3: Bank acknowledges request
- TC4: Unrelated credit
- Safety Checklist: Gating, Invalidation upon edit, Idempotency, Ambiguous credit handling.
"""
import pytest
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.account import Account, AccountTier
from backend.app.models.tariff import TariffRule
from backend.app.models.statement import Statement, Transaction
from backend.app.models.audit import AuditFinding
from backend.app.models.reversal import ReversalRequest
from backend.app.models.verification import VerificationResult

from backend.app.services.audit_service import audit_service
from backend.app.services.reversal_service import reversal_service
from backend.app.services.verification_service import verification_service
from backend.app.mock_bank.synthetic_data import sha256_hash


@pytest.mark.asyncio
async def test_tc1_wrong_minimum_balance_fee(db_session):
    """TC1 — Wrong minimum-balance fee:
    Statement ADB ($1,840.50) satisfies the $1,500.00 waiver threshold.
    Audit engine must flag the $12.00 monthly fee with evidence.
    Reversal draft is created.
    Submission to mock bank MUST require human approval first.
    """
    # 1. Fetch synthetic statement with minimum balance violation
    stmt_q = (
        select(Statement)
        .where(
            Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
            Statement.is_subsequent_statement.is_(False)
        )
        .options(selectinload(Statement.account).selectinload(Account.tier))
    )
    res = await db_session.execute(stmt_q)
    statement = res.scalar_one()

    # Preconditions / Fixture IDs
    fixture_account_id = statement.account_id
    fixture_statement_id = statement.id
    adb = statement.average_daily_balance
    tier_waiver = statement.account.tier.min_balance_waiver

    assert adb >= tier_waiver, f"Precondition failed: ADB {adb} must be >= {tier_waiver}"

    # 2. Run actual audit engine
    findings = await audit_service.audit_statement(db_session, statement.id)

    # 3. Verify fee is flagged with evidence
    maintenance_findings = [f for f in findings if f.rule_category == "MONTHLY_MAINTENANCE"]
    assert len(maintenance_findings) == 1, "Expected exactly 1 monthly maintenance fee finding"
    finding = maintenance_findings[0]

    assert finding.fee_amount == 12.00
    assert finding.potential_refund_amount == 12.00
    assert finding.severity == "HIGH"
    assert finding.status == "FLAGGED"
    assert "average_daily_balance" in finding.evidence_data
    assert finding.evidence_data["average_daily_balance"] == adb
    assert finding.evidence_data["min_balance_waiver_threshold"] == tier_waiver

    # 4. Draft reversal request
    reversal = await reversal_service.draft_reversal(db_session, finding.id, prepared_by="Compliance Auditor")
    assert reversal.status == "PENDING_APPROVAL"
    assert reversal.requested_amount == 12.00
    assert "DISPUTE NOTICE" in reversal.rationale_letter

    # 5. Verify submission strictly requires human approval
    with pytest.raises(ValueError) as excinfo:
        await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert "Explicit human approval is required prior to submission" in str(excinfo.value)


@pytest.mark.asyncio
async def test_tc2_tariff_of_different_account_tier(db_session):
    """TC2 — Tariff of a different account tier:
    Use a synthetic account with a known tier (Small Business Commercial, TIER_SMB)
    where a fee is valid under its own tier ($30 monthly fee charged when ADB is $3,200 < $5,000 waiver).
    Under Everyday Checking ($1,500 waiver), it would have been waived.
    The engine must NOT falsely flag the fee and no reversal draft must be created.
    """
    # 1. Fetch TIER_SMB
    tier_q = select(AccountTier).where(AccountTier.code == "TIER_SMB")
    tier_res = await db_session.execute(tier_q)
    smb_tier = tier_res.scalar_one()

    # 2. Create synthetic SMB account with ADB = $3,200 (under SMB $5,000 waiver)
    acc = Account(
        account_number="ACT-TC2-SMB-VALID-01",
        holder_name="Pioneer Wholesale Supplies",
        bank_name="Apex National Bank",
        tier_id=smb_tier.id,
        current_balance=3200.00,
        source_id="SYNTH-ACC-TC2-01"
    )
    db_session.add(acc)
    await db_session.flush()

    # 3. Create statement where ADB is $3,200.00 and $30 monthly fee was charged
    stmt_meta = {
        "account_id": acc.id,
        "statement_period_start": date(2024, 3, 1),
        "statement_period_end": date(2024, 3, 31),
        "opening_balance": 3500.00,
        "closing_balance": 3170.00,
        "average_daily_balance": 3200.00,  # Below $5,000 waiver!
        "total_qualifying_direct_deposits": 0.0,
        "is_subsequent_statement": False,
        "source_id": "SYNTH-STMT-TC2-SMB",
        "source_filename": "Pioneer_SMB_March2024.pdf",
        "raw_statement_hash": sha256_hash("SYNTH-STMT-TC2-SMB")
    }
    stmt = Statement(**stmt_meta)
    db_session.add(stmt)
    await db_session.flush()

    # Transaction: legitimate $30 monthly fee under SMB tier
    fee_tx = Transaction(
        statement_id=stmt.id,
        transaction_date=date(2024, 3, 31),
        posting_date=date(2024, 3, 31),
        description="Monthly Maintenance Charge - Commercial",
        transaction_type="FEE",
        amount=30.00,
        balance_after=3170.00,
        raw_category="BANK_FEE",
        source_transaction_id="TXN-TC2-FEE-30"
    )
    db_session.add(fee_tx)
    await db_session.commit()

    # 4. Run audit engine on this statement
    findings = await audit_service.audit_statement(db_session, stmt.id)

    # 5. Assert: The fee is valid under SMB tier ($3,200 < $5,000), so NO maintenance fee finding
    maintenance_findings = [f for f in findings if f.rule_category == "MONTHLY_MAINTENANCE"]
    assert len(maintenance_findings) == 0, (
        f"TC2 FAILED: Fee was falsely flagged under SMB tier! Findings: {maintenance_findings}"
    )

    # 6. Assert: No reversal draft is created
    reversal_q = select(ReversalRequest).where(ReversalRequest.account_id == acc.id)
    rev_res = await db_session.execute(reversal_q)
    assert len(list(rev_res.scalars().all())) == 0


@pytest.mark.asyncio
async def test_tc3_bank_acknowledges_request_no_refund_remains_pending(db_session):
    """TC3 — Bank acknowledges request:
    Submit an approved reversal to mock bank portal.
    Simulate acknowledgement (returns mock ticket).
    Verify against a subsequent statement that has NO matching credit.
    The reversal request must remain pending (ACKNOWLEDGED), never marked credited/settled.
    """
    # 1. Get initial statement finding
    stmt_q = select(Statement).where(
        Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
        Statement.is_subsequent_statement.is_(False)
    )
    res = await db_session.execute(stmt_q)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    finding = next(f for f in findings if f.fee_amount == 12.00)

    # 2. Draft and approve reversal
    reversal = await reversal_service.draft_reversal(db_session, finding.id)
    await reversal_service.record_approval(
        db_session,
        reversal.id,
        action="APPROVE",
        approved_by_user="Compliance Officer TC3",
        notes="Approved for mock submission."
    )

    # 3. Submit to mock bank portal
    ack = await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert ack["status"] == "ACCEPTED"
    assert "ticket_id" in ack
    assert reversal.status == "ACKNOWLEDGED"

    # 4. Create a subsequent statement with NO matching credit (only expenses and standard debits)
    subsequent_no_credit = Statement(
        account_id=statement.account_id,
        statement_period_start=date(2024, 4, 1),
        statement_period_end=date(2024, 4, 30),
        opening_balance=1936.20,
        closing_balance=1800.00,
        average_daily_balance=1850.00,
        total_qualifying_direct_deposits=0.0,
        is_subsequent_statement=True,
        source_id="SYNTH-STMT-TC3-NO-REFUND",
        source_filename="Everyday_April2024_NoRefund.pdf",
        raw_statement_hash=sha256_hash("SYNTH-STMT-TC3-NO-REFUND")
    )
    db_session.add(subsequent_no_credit)
    await db_session.flush()

    # Only ordinary transactions, zero refund credits
    ordinary_tx = Transaction(
        statement_id=subsequent_no_credit.id,
        transaction_date=date(2024, 4, 15),
        posting_date=date(2024, 4, 15),
        description="Electric Utility Bill Payment",
        transaction_type="DEBIT",
        amount=136.20,
        balance_after=1800.00,
        raw_category="UTILITIES",
        source_transaction_id="TXN-TC3-ORDINARY"
    )
    db_session.add(ordinary_tx)
    await db_session.commit()

    # 5. Run verification against this statement
    verification = await verification_service.verify_reversal(
        db_session,
        reversal_id=reversal.id,
        subsequent_statement_id=subsequent_no_credit.id
    )

    # 6. Assert: Result must NOT be verified, must be NOT_FOUND_IN_SUBSEQUENT
    assert verification.is_verified is False
    assert verification.verification_status == "NOT_FOUND_IN_SUBSEQUENT"
    assert verification.verified_amount == 0.0

    # 7. Crucial: Request must remain pending, NEVER credited or settled!
    reloaded_rev = await db_session.get(ReversalRequest, reversal.id)
    assert reloaded_rev.status == "ACKNOWLEDGED", (
        f"TC3 FAILED: Reversal status should remain ACKNOWLEDGED (pending), but is {reloaded_rev.status}"
    )

    # Finding status must remain SUBMITTED, not REVERSED
    reloaded_finding = await db_session.get(AuditFinding, finding.id)
    assert reloaded_finding.status == "SUBMITTED"


@pytest.mark.asyncio
async def test_tc4_unrelated_credit_not_matched(db_session):
    """TC4 — Unrelated credit:
    Provide a subsequent statement with an unrelated credit (e.g. merchant refund or payroll).
    Verify that it is NOT matched as the fee reversal and the request remains pending/unresolved.
    """
    # 1. Get initial statement finding (e.g. $35 overdraft fee)
    stmt_q = select(Statement).where(
        Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
        Statement.is_subsequent_statement.is_(False)
    )
    res = await db_session.execute(stmt_q)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    od_finding = next(f for f in findings if f.fee_amount == 35.00)

    # 2. Draft, approve, and submit reversal for $35.00
    reversal = await reversal_service.draft_reversal(db_session, od_finding.id)
    await reversal_service.record_approval(
        db_session,
        reversal.id,
        action="APPROVE",
        approved_by_user="Compliance Officer TC4"
    )
    await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert reversal.status == "ACKNOWLEDGED"

    # 3. Create subsequent statement containing UNRELATED credits:
    # - Credit 1: $1,250.00 Payroll direct deposit
    # - Credit 2: $35.00 Amazon merchandise store return (same dollar amount, but unrelated commercial return!)
    # - Credit 3: $35.00 Venmo peer-to-peer transfer
    subsequent_unrelated = Statement(
        account_id=statement.account_id,
        statement_period_start=date(2024, 4, 1),
        statement_period_end=date(2024, 4, 30),
        opening_balance=1936.20,
        closing_balance=3256.20,
        average_daily_balance=2500.00,
        total_qualifying_direct_deposits=1250.00,
        is_subsequent_statement=True,
        source_id="SYNTH-STMT-TC4-UNRELATED",
        source_filename="Everyday_April2024_UnrelatedCredits.pdf",
        raw_statement_hash=sha256_hash("SYNTH-STMT-TC4-UNRELATED")
    )
    db_session.add(subsequent_unrelated)
    await db_session.flush()

    unrelated_tx1 = Transaction(
        statement_id=subsequent_unrelated.id,
        transaction_date=date(2024, 4, 5),
        posting_date=date(2024, 4, 5),
        description="Payroll Direct Deposit - ACME Corporation",
        transaction_type="CREDIT",
        amount=1250.00,
        balance_after=3186.20,
        raw_category="PAYROLL",
        source_transaction_id="TXN-TC4-PAYROLL"
    )
    unrelated_tx2 = Transaction(
        statement_id=subsequent_unrelated.id,
        transaction_date=date(2024, 4, 12),
        posting_date=date(2024, 4, 12),
        description="Amazon.com Merchant Refund - Shoes Return",
        transaction_type="REFUND",
        amount=35.00,  # Exact same dollar amount, but commercial return!
        balance_after=3221.20,
        raw_category="SHOPPING",
        source_transaction_id="TXN-TC4-AMAZON-REFUND"
    )
    unrelated_tx3 = Transaction(
        statement_id=subsequent_unrelated.id,
        transaction_date=date(2024, 4, 18),
        posting_date=date(2024, 4, 18),
        description="Venmo Transfer from Sarah - Dinner Split",
        transaction_type="CREDIT",
        amount=35.00,  # Exact same dollar amount, but P2P transfer!
        balance_after=3256.20,
        raw_category="TRANSFER",
        source_transaction_id="TXN-TC4-VENMO"
    )
    db_session.add_all([unrelated_tx1, unrelated_tx2, unrelated_tx3])
    await db_session.commit()

    # 4. Run verification
    verification = await verification_service.verify_reversal(
        db_session,
        reversal_id=reversal.id,
        subsequent_statement_id=subsequent_unrelated.id
    )

    # 5. Assert: The unrelated credits MUST NOT be matched as the fee reversal!
    assert verification.is_verified is False
    assert verification.verification_status in ("NOT_FOUND_IN_SUBSEQUENT", "AMBIGUOUS_UNRESOLVED")
    assert verification.refund_transaction_id is None, "Must not link to unrelated transaction ID"

    # 6. Assert: Reversal request remains pending (ACKNOWLEDGED), never settled
    reloaded_rev = await db_session.get(ReversalRequest, reversal.id)
    assert reloaded_rev.status == "ACKNOWLEDGED"

    reloaded_finding = await db_session.get(AuditFinding, od_finding.id)
    assert reloaded_finding.status == "SUBMITTED"


@pytest.mark.asyncio
async def test_safety_checklist_invalidation_upon_edit(db_session):
    """Safety Checklist: Editing a draft invalidates prior human approval."""
    # 1. Create and approve a reversal
    stmt_q = select(Statement).where(Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY")
    res = await db_session.execute(stmt_q)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    finding = findings[0]

    reversal = await reversal_service.draft_reversal(db_session, finding.id)
    await reversal_service.record_approval(db_session, reversal.id, "APPROVE", "Lead Auditor")
    assert reversal.status == "APPROVED"

    # 2. Modify the draft
    updated = await reversal_service.update_draft(
        db=db_session,
        reversal_id=reversal.id,
        rationale_letter="Updated dispute rationale with revised evidence.",
        editor_user="Assistant Auditor"
    )

    # 3. Assert: Prior approval was invalidated, status reset to PENDING_APPROVAL
    assert updated.status == "PENDING_APPROVAL"
    assert updated.rationale_letter == "Updated dispute rationale with revised evidence."

    # Invalidation event logged in audit trail
    invalidation_events = [a for a in updated.approvals if a.action == "APPROVAL_INVALIDATED"]
    assert len(invalidation_events) >= 1
    assert invalidation_events[-1].approved_by_user == "Assistant Auditor"

    # 4. Attempting to submit without re-approval MUST fail!
    with pytest.raises(ValueError) as exc:
        await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert "Explicit human approval is required prior to submission" in str(exc.value)


@pytest.mark.asyncio
async def test_safety_checklist_prevent_duplicate_submission(db_session):
    """Safety Checklist: Retries cannot duplicate submissions."""
    stmt_q = select(Statement).where(Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY")
    res = await db_session.execute(stmt_q)
    statement = res.scalar_one()

    findings = await audit_service.audit_statement(db_session, statement.id)
    finding = findings[0]

    reversal = await reversal_service.draft_reversal(db_session, finding.id)
    await reversal_service.record_approval(db_session, reversal.id, "APPROVE", "Lead Auditor")
    await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert reversal.status == "ACKNOWLEDGED"

    # Attempting to submit again (retry) MUST fail and not duplicate submission
    with pytest.raises(ValueError) as exc:
        await reversal_service.submit_to_mock_bank(db_session, reversal.id)
    assert "already submitted" in str(exc.value).lower()
    assert "duplicate submissions are strictly prohibited" in str(exc.value).lower()
