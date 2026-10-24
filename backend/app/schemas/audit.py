"""Pydantic schemas for Audit Findings."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.statement import TransactionResponse


class AuditFindingResponse(BaseModel):
    id: str
    statement_id: str
    transaction_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_category: str
    fee_amount: float
    potential_refund_amount: float
    severity: str
    status: str
    violation_title: str
    violation_reason: str
    evidence_data: Dict[str, Any]
    source_evidence_snapshot: Optional[str] = None
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    transaction: Optional[TransactionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AuditRunSummary(BaseModel):
    statement_id: str
    findings_count: int
    total_fee_amount: float
    total_potential_refund: float
    findings: List[AuditFindingResponse]
