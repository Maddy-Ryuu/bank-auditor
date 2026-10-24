"""Pydantic schemas for Mock Bank Portal interaction."""
from typing import Dict, Any, List
from pydantic import BaseModel


class MockBankPortalStatusResponse(BaseModel):
    gateway_name: str
    status: str
    endpoint: str
    is_simulation: bool
    mock_settlement_cycle: str
    total_reversals_processed: int
    pending_reversals_queued: int


class MockBankPortalSubmissionRequest(BaseModel):
    reversal_id: str
