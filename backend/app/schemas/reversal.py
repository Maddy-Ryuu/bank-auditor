"""Pydantic schemas for Reversals, Approvals, and Mock Bank Acknowledgements."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.audit import AuditFindingResponse


class ApprovalEventResponse(BaseModel):
    id: str
    reversal_request_id: str
    action: str
    approved_by_user: str
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    event_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalActionRequest(BaseModel):
    action: str  # APPROVE, REJECT, REQUEST_REVISION
    approved_by_user: str = "Compliance Officer"
    notes: Optional[str] = None


class ReversalUpdateRequest(BaseModel):
    requested_amount: Optional[float] = None
    rationale_letter: Optional[str] = None
    editor_user: str = "Compliance Officer"


class MockBankAckResponse(BaseModel):
    id: str
    reversal_request_id: str
    mock_bank_ticket_id: str
    status_received: str
    portal_endpoint_called: str
    acknowledgement_payload: Dict[str, Any]
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReversalRequestResponse(BaseModel):
    id: str
    finding_id: str
    account_id: str
    reference_number: str
    requested_amount: float
    rationale_letter: str
    status: str
    prepared_by: str
    created_at: datetime
    updated_at: datetime
    finding: Optional[AuditFindingResponse] = None
    approvals: List[ApprovalEventResponse] = []
    mock_ack: Optional[MockBankAckResponse] = None

    model_config = ConfigDict(from_attributes=True)
