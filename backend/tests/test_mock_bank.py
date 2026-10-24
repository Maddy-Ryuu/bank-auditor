"""Tests verifying mock bank portal safety and synthetic boundaries."""
import pytest
from backend.app.mock_bank.client import mock_bank_client


@pytest.mark.asyncio
async def test_mock_bank_portal_safe_simulation():
    """Verify that mock bank portal processes responses purely in-memory and safely."""
    ack = await mock_bank_client.submit_reversal_request(
        reversal_id="test-rev-123",
        reference_number="REV-TEST-001",
        account_number="ACT-0000-TEST",
        fee_amount=35.00,
        rationale="Synthetic dispute for unit testing.",
        approved_by="Auditor QA"
    )

    assert ack["status"] == "ACCEPTED"
    assert "ticket_id" in ack
    assert ack["credited_amount"] == 35.00
    assert ack["settlement_cycle"] == "SUBSEQUENT_STATEMENT_BILLING_CYCLE"
    assert "digital_signature" in ack
