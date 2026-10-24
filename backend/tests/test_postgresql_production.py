"""PostgreSQL Production Compatibility Test Suite.

Executes real migrations, schema verification, asyncpg driver connectivity,
UUID/JSON handling, and the complete audit/approval/mock submission/reconciliation
lifecycle against an actual live PostgreSQL 16 instance.
"""
import os
import tempfile
import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from alembic.config import Config
from alembic import command

from backend.app.models.account import Account, AccountTier
from backend.app.models.tariff import TariffRule
from backend.app.models.statement import Statement, Transaction
from backend.app.models.audit import AuditFinding
from backend.app.models.reversal import ReversalRequest, ApprovalEvent, MockBankAck
from backend.app.models.verification import VerificationResult

from backend.app.services.audit_service import audit_service
from backend.app.services.reversal_service import reversal_service
from backend.app.services.verification_service import verification_service
from backend.app.seed_data import seed_database
from backend.app.mock_bank.synthetic_data import sha256_hash

import pgserver


@pytest.fixture(scope="module")
def postgres_instance():
    """Spin up a live, isolated PostgreSQL instance."""
    temp_dir = tempfile.mkdtemp(prefix="pg_test_")
    srv = pgserver.get_server(temp_dir)
    sync_uri = srv.get_uri()
    async_uri = sync_uri.replace("postgresql://", "postgresql+asyncpg://")

    yield {"sync_uri": sync_uri, "async_uri": async_uri, "temp_dir": temp_dir}

    try:
        srv.cleanup()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_postgresql_empty_db_migration(postgres_instance):
    """Test 1: Run Alembic migrations from scratch on an empty PostgreSQL database."""
    sync_url = postgres_instance["sync_uri"]

    alembic_cfg = Config(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")))
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    alembic_cfg.set_main_option("script_location", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic")))

    # Upgrade to head on PostgreSQL
    command.upgrade(alembic_cfg, "head")

    # Connect and verify all 11 tables exist in PostgreSQL
    engine = create_async_engine(postgres_instance["async_uri"])
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [row[0] for row in res.fetchall()]

    await engine.dispose()

    expected_tables = {
        "account_tiers",
        "accounts",
        "tariff_rules",
        "statements",
        "transactions",
        "audit_findings",
        "reversal_requests",
        "approval_events",
        "mock_bank_acks",
        "verification_results",
        "test_runs",
        "alembic_version"
    }

    assert expected_tables.issubset(set(tables)), (
        f"Missing tables in PostgreSQL migration! Found: {tables}"
    )


@pytest.mark.asyncio
async def test_postgresql_seed_and_crud(postgres_instance):
    """Test 2: Seed synthetic dataset into PostgreSQL and verify JSON, UUID, and relationship handling."""
    engine = create_async_engine(postgres_instance["async_uri"])
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Seed into PostgreSQL
        await seed_database(session, run_initial_audit=False)

        # Verify tiers
        tiers_res = await session.execute(select(AccountTier))
        tiers = list(tiers_res.scalars().all())
        assert len(tiers) == 3

        # Verify accounts
        accs_res = await session.execute(select(Account).options(selectinload(Account.tier)))
        accs = list(accs_res.scalars().all())
        assert len(accs) == 3
        for acc in accs:
            assert acc.tier is not None
            assert len(acc.id) == 36  # Valid UUID string

        # Verify statements & transactions
        stmts_res = await session.execute(select(Statement).options(selectinload(Statement.transactions)))
        stmts = list(stmts_res.scalars().all())
        assert len(stmts) == 6  # 3 initial + 3 subsequent
        total_txs = sum(len(s.transactions) for s in stmts)
        assert total_txs > 0

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_full_audit_workflow(postgres_instance):
    """Test 3: Full audit, approval gating, mock submission, and reconciliation workflow in PostgreSQL."""
    engine = create_async_engine(postgres_instance["async_uri"])
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Audit initial Everyday checking statement
        stmt_q = select(Statement).where(
            Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
            Statement.is_subsequent_statement.is_(False)
        )
        stmt_res = await session.execute(stmt_q)
        statement = stmt_res.scalar_one()

        findings = await audit_service.audit_statement(session, statement.id)
        assert len(findings) >= 3

        # Verify JSON evidence handling in PostgreSQL
        for f in findings:
            assert isinstance(f.evidence_data, dict)
            assert "rule_applied" in f.evidence_data

        od_finding = next(f for f in findings if f.fee_amount == 35.00)

        # 2. Draft reversal in PostgreSQL
        reversal = await reversal_service.draft_reversal(session, od_finding.id, prepared_by="PostgreSQL Auditor")
        assert reversal.status == "PENDING_APPROVAL"
        assert len(reversal.id) == 36

        # 3. Server-side approval gating in PostgreSQL
        with pytest.raises(ValueError) as exc:
            await reversal_service.submit_to_mock_bank(session, reversal.id)
        assert "Explicit human approval is required" in str(exc.value)

        # 4. Human approval in PostgreSQL
        approved = await reversal_service.record_approval(
            session,
            reversal.id,
            action="APPROVE",
            approved_by_user="PG Compliance Officer",
            notes="Validated on PostgreSQL 16."
        )
        assert approved.status == "APPROVED"
        assert len(approved.approvals) == 1

        # 5. Safety rule: Editing draft invalidates prior approval in PostgreSQL
        edited = await reversal_service.update_draft(
            session,
            reversal.id,
            rationale_letter="Updated rationale for PostgreSQL verification test.",
            editor_user="Senior QA"
        )
        assert edited.status == "PENDING_APPROVAL"
        assert len(edited.approvals) == 2  # Original approve + invalidation event

        # Re-approve
        await reversal_service.record_approval(session, reversal.id, "APPROVE", "Lead QA Officer")

        # 6. Submit to Mock Bank Gateway
        ack = await reversal_service.submit_to_mock_bank(session, reversal.id)
        assert ack["status"] == "ACCEPTED"
        assert "ticket_id" in ack
        assert reversal.status == "ACKNOWLEDGED"

        # 7. Duplicate submission prevention in PostgreSQL
        with pytest.raises(ValueError) as dup_exc:
            await reversal_service.submit_to_mock_bank(session, reversal.id)
        assert "already submitted" in str(dup_exc.value).lower()

        # 8. Reconcile refund on subsequent statement in PostgreSQL
        verification = await verification_service.verify_reversal(session, reversal.id)
        assert verification.is_verified is True
        assert verification.verification_status == "MATCHED_EXACT"
        assert verification.verified_amount == 35.00
        assert reversal.status == "SETTLED"

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_tc2_tier_differentiation(postgres_instance):
    """Test 4: TC2 on PostgreSQL — Verify fee legitimate under SMB tier is NOT flagged."""
    engine = create_async_engine(postgres_instance["async_uri"])
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        tier_q = select(AccountTier).where(AccountTier.code == "TIER_SMB")
        smb_tier = (await session.execute(tier_q)).scalar_one()

        acc = Account(
            account_number="ACT-PG-SMB-VALID-01",
            holder_name="PG Enterprise Supplies",
            bank_name="Apex National Bank",
            tier_id=smb_tier.id,
            current_balance=3200.00,
            source_id="SYNTH-ACC-PG-SMB-01"
        )
        session.add(acc)
        await session.flush()

        stmt = Statement(
            account_id=acc.id,
            statement_period_start=date(2024, 3, 1),
            statement_period_end=date(2024, 3, 31),
            opening_balance=3500.00,
            closing_balance=3170.00,
            average_daily_balance=3200.00,
            total_qualifying_direct_deposits=0.0,
            is_subsequent_statement=False,
            source_id="SYNTH-STMT-PG-TC2-SMB",
            source_filename="PG_SMB_March2024.pdf",
            raw_statement_hash=sha256_hash("SYNTH-STMT-PG-TC2-SMB")
        )
        session.add(stmt)
        await session.flush()

        fee_tx = Transaction(
            statement_id=stmt.id,
            transaction_date=date(2024, 3, 31),
            posting_date=date(2024, 3, 31),
            description="Monthly Maintenance Charge - Commercial",
            transaction_type="FEE",
            amount=30.00,
            balance_after=3170.00,
            raw_category="BANK_FEE",
            source_transaction_id="TXN-PG-TC2-FEE-30"
        )
        session.add(fee_tx)
        await session.commit()

        findings = await audit_service.audit_statement(session, stmt.id)
        maint_findings = [f for f in findings if f.rule_category == "MONTHLY_MAINTENANCE"]
        assert len(maint_findings) == 0, "Fee should not be flagged under SMB tier on PostgreSQL"

        reversals = (await session.execute(
            select(ReversalRequest).where(ReversalRequest.account_id == acc.id)
        )).scalars().all()
        assert len(list(reversals)) == 0

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_tc3_and_tc4_reconciliation_safety(postgres_instance):
    """Test 5: TC3 & TC4 on PostgreSQL — Missing or unrelated credits must leave request pending/unresolved."""
    engine = create_async_engine(postgres_instance["async_uri"])
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        stmt_q = select(Statement).where(
            Statement.source_id == "SYNTH-STMT-2024-03-EVERYDAY",
            Statement.is_subsequent_statement.is_(False)
        )
        stmt = (await session.execute(stmt_q)).scalar_one()
        findings = await audit_service.audit_statement(session, stmt.id)
        maint_finding = next(f for f in findings if f.rule_category == "MONTHLY_MAINTENANCE")

        # Draft, approve, and submit
        rev = await reversal_service.draft_reversal(session, maint_finding.id, prepared_by="PG TC3/TC4 Auditor")
        await reversal_service.record_approval(session, rev.id, "APPROVE", "PG Auditor")
        await reversal_service.submit_to_mock_bank(session, rev.id)
        assert rev.status == "ACKNOWLEDGED"

        # TC3 check: Subsequent statement with NO refund credit
        no_refund_stmt = Statement(
            account_id=stmt.account_id,
            statement_period_start=date(2024, 5, 1),
            statement_period_end=date(2024, 5, 31),
            opening_balance=2000.00,
            closing_balance=1850.00,
            average_daily_balance=1900.00,
            is_subsequent_statement=True,
            source_id="SYNTH-STMT-PG-TC3-NO-REFUND",
            source_filename="PG_May2024_NoRefund.pdf",
            raw_statement_hash=sha256_hash("SYNTH-STMT-PG-TC3-NO-REFUND")
        )
        session.add(no_refund_stmt)
        await session.flush()

        v3 = await verification_service.verify_reversal(session, rev.id, no_refund_stmt.id)
        assert v3.is_verified is False
        assert v3.verification_status == "NOT_FOUND_IN_SUBSEQUENT"
        assert rev.status == "ACKNOWLEDGED"  # Must remain pending!

        # TC4 check: Subsequent statement with unrelated credit ($12.00 merchant refund)
        unrelated_stmt = Statement(
            account_id=stmt.account_id,
            statement_period_start=date(2024, 6, 1),
            statement_period_end=date(2024, 6, 30),
            opening_balance=1850.00,
            closing_balance=1862.00,
            average_daily_balance=1855.00,
            is_subsequent_statement=True,
            source_id="SYNTH-STMT-PG-TC4-UNRELATED",
            source_filename="PG_June2024_Unrelated.pdf",
            raw_statement_hash=sha256_hash("SYNTH-STMT-PG-TC4-UNRELATED")
        )
        session.add(unrelated_stmt)
        await session.flush()

        unrelated_tx = Transaction(
            statement_id=unrelated_stmt.id,
            transaction_date=date(2024, 6, 15),
            posting_date=date(2024, 6, 15),
            description="Target Store Return - Item Refund",
            transaction_type="REFUND",
            amount=12.00,
            balance_after=1862.00,
            raw_category="SHOPPING",
            source_transaction_id="TXN-PG-TC4-TARGET"
        )
        session.add(unrelated_tx)
        await session.commit()

        v4 = await verification_service.verify_reversal(session, rev.id, unrelated_stmt.id)
        assert v4.is_verified is False
        assert v4.verification_status in ("NOT_FOUND_IN_SUBSEQUENT", "AMBIGUOUS_UNRESOLVED")
        assert rev.status == "ACKNOWLEDGED"  # Never settled with unrelated credit

    await engine.dispose()

