"""Mock Bank Portal API client and simulation engine."""
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from backend.app.config import settings
from backend.app.logging_config import logger


class MockBankPortalClient:
    """Simulated Mock Bank Gateway.
    
    IMPORTANT: Under NO circumstances are requests sent to external bank infrastructure.
    All calls are processed safely against this isolated synthetic mock portal.
    """

    def __init__(self):
        self.portal_name = settings.MOCK_BANK_PORTAL_NAME
        self.api_endpoint = "https://mock-gateway.internal.apexnational.com/api/v1/disputes/reversal"

    async def submit_reversal_request(
        self,
        reversal_id: str,
        reference_number: str,
        account_number: str,
        fee_amount: float,
        rationale: str,
        approved_by: str
    ) -> Dict[str, Any]:
        """Simulates submission to the mock bank dispute gateway."""
        logger.info(
            f"[MOCK BANK PORTAL] Submitting reversal {reference_number} for account {account_number} (${fee_amount:.2f}). "
            f"Approved by: {approved_by}"
        )

        # Realistic mock latency simulation
        if settings.MOCK_BANK_ACK_LATENCY_MS > 0:
            await asyncio.sleep(settings.MOCK_BANK_ACK_LATENCY_MS / 1000.0)

        ticket_suffix = uuid.uuid4().hex[:8].upper()
        mock_ticket_id = f"MB-TKT-{datetime.now(timezone.utc).strftime('%Y%m')}-{ticket_suffix}"

        ack_payload = {
            "ticket_id": mock_ticket_id,
            "bank_gateway": self.portal_name,
            "status": "ACCEPTED",
            "resolution_status": "APPROVED_FOR_STATEMENT_CREDIT",
            "account_number": account_number,
            "dispute_reference": reference_number,
            "reversal_id": reversal_id,
            "credited_amount": fee_amount,
            "currency": "USD",
            "settlement_cycle": "SUBSEQUENT_STATEMENT_BILLING_CYCLE",
            "bank_notes": (
                "Mock Bank Operations Review: Client dispute evidence reviewed and validated against tariff criteria. "
                "Credit will post to the subsequent account statement."
            ),
            "submitted_rationale_preview": rationale[:120] + "...",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "digital_signature": f"SHA256:MOCK-SIG-{uuid.uuid4().hex}",
        }

        logger.info(f"[MOCK BANK PORTAL] Dispute acknowledged. Ticket: {mock_ticket_id}, Status: ACCEPTED")
        return ack_payload


mock_bank_client = MockBankPortalClient()
