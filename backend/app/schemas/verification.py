"""Pydantic schemas for Verification Results."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VerificationResultResponse(BaseModel):
    id: str
    reversal_request_id: str
    subsequent_statement_id: str
    refund_transaction_id: Optional[str] = None
    is_verified: bool
    verified_amount: float
    expected_amount: float
    discrepancy_amount: float
    verification_status: str
    notes: Optional[str] = None
    verified_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationRunRequest(BaseModel):
    reversal_id: str
    subsequent_statement_id: Optional[str] = None
