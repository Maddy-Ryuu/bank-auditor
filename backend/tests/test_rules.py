"""Unit tests for individual audit rules."""
import pytest
from datetime import date
from types import SimpleNamespace
from backend.app.rules.monthly_maintenance import MonthlyMaintenanceFeeRule
from backend.app.rules.overdraft_fee import OverdraftFeeRule
from backend.app.rules.paper_statement_fee import PaperStatementFeeRule
from backend.app.rules.wire_transfer_fee import WireTransferFeeRule
from backend.app.rules.foreign_transaction import ForeignTransactionFeeRule


def test_monthly_maintenance_rule_waived_by_balance():
    rule = MonthlyMaintenanceFeeRule()
    tier = SimpleNamespace(min_balance_waiver=1500.0, min_direct_deposit_waiver=500.0, name="Everyday")
    statement = SimpleNamespace(average_daily_balance=1800.0, total_qualifying_direct_deposits=0.0)
    tx = SimpleNamespace(
        id="tx-1",
        transaction_date=date(2024, 3, 31),
        description="Monthly Maintenance Fee",
        transaction_type="FEE",
        amount=12.00,
        source_transaction_id="TX-123"
    )

    findings = rule.evaluate(statement, None, tier, [], [tx])
    assert len(findings) == 1
    assert findings[0].fee_amount == 12.00
    assert findings[0].potential_refund_amount == 12.00
    assert "exceeding the $1,500.00 waiver requirement" in findings[0].violation_reason


def test_monthly_maintenance_rule_no_waiver():
    rule = MonthlyMaintenanceFeeRule()
    tier = SimpleNamespace(min_balance_waiver=1500.0, min_direct_deposit_waiver=500.0, name="Everyday")
    statement = SimpleNamespace(average_daily_balance=800.0, total_qualifying_direct_deposits=200.0)
    tx = SimpleNamespace(
        id="tx-1",
        transaction_date=date(2024, 3, 31),
        description="Monthly Maintenance Fee",
        transaction_type="FEE",
        amount=12.00,
        source_transaction_id="TX-123"
    )

    findings = rule.evaluate(statement, None, tier, [], [tx])
    assert len(findings) == 0


def test_overdraft_rule_daily_cap_exceeded():
    rule = OverdraftFeeRule()
    tier = SimpleNamespace(max_daily_overdraft_fees=3, overdraft_fee_amount=35.0, overdraft_threshold_cents=500)
    statement = SimpleNamespace()
    d = date(2024, 3, 15)

    txs = [
        SimpleNamespace(id="t1", transaction_date=d, description="Overdraft Fee 1", transaction_type="FEE", amount=35.0, balance_after=-50.0, source_transaction_id="T1"),
        SimpleNamespace(id="t2", transaction_date=d, description="Overdraft Fee 2", transaction_type="FEE", amount=35.0, balance_after=-85.0, source_transaction_id="T2"),
        SimpleNamespace(id="t3", transaction_date=d, description="Overdraft Fee 3", transaction_type="FEE", amount=35.0, balance_after=-120.0, source_transaction_id="T3"),
        SimpleNamespace(id="t4", transaction_date=d, description="Overdraft Fee 4", transaction_type="FEE", amount=35.0, balance_after=-155.0, source_transaction_id="T4"),
    ]

    findings = rule.evaluate(statement, None, tier, [], txs)
    assert len(findings) == 1
    assert findings[0].transaction_id == "t4"
    assert findings[0].fee_amount == 35.0
    assert "exceeding the contractual tier limit of 3" in findings[0].violation_reason


def test_paper_statement_rule_enrolled():
    rule = PaperStatementFeeRule()
    account = SimpleNamespace(account_number="ACT-1234", electronic_statements_enrolled=True)
    tx = SimpleNamespace(
        id="t-p1",
        transaction_date=date(2024, 3, 28),
        description="Paper Statement Fee",
        transaction_type="FEE",
        amount=3.0,
        source_transaction_id="TP1"
    )

    findings = rule.evaluate(None, account, None, [], [tx])
    assert len(findings) == 1
    assert findings[0].fee_amount == 3.0
    assert "actively enrolled in paperless" in findings[0].violation_reason


def test_wire_transfer_rule_complimentary():
    rule = WireTransferFeeRule()
    tier = SimpleNamespace(wire_incoming_domestic_fee=0.0, wire_outgoing_domestic_fee=25.0, name="Premier")
    tx = SimpleNamespace(
        id="w-1",
        transaction_date=date(2024, 3, 10),
        description="Incoming Wire Fee - Domestic",
        transaction_type="FEE",
        amount=15.0,
        source_transaction_id="W1"
    )

    findings = rule.evaluate(None, None, tier, [], [tx])
    assert len(findings) == 1
    assert findings[0].potential_refund_amount == 15.0
    assert "complimentary incoming domestic wires" in findings[0].violation_reason
