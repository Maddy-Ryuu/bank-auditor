"""Pydantic schemas for Test Runs."""
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TestRunResponse(BaseModel):
    id: str
    test_suite_name: str
    run_type: str
    status: str
    findings_detected_count: int
    total_fee_amount_audited: float
    potential_recovery_amount: float
    execution_duration_ms: int
    details: Dict[str, Any]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
