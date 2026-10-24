"""Base rule abstraction and rule evaluation result."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RuleEvaluationFinding(BaseModel):
    """Structured result returned by a rule evaluation."""
    rule_category: str
    fee_amount: float
    potential_refund_amount: float
    severity: str = "HIGH"
    violation_title: str
    violation_reason: str
    evidence_data: Dict[str, Any]
    transaction_id: Optional[str] = None
    rule_id: Optional[str] = None
    source_evidence_snapshot: Optional[str] = None


class BaseAuditRule(ABC):
    """Abstract base class for all bank fee audit rules."""
    rule_id: str
    name: str
    category: str
    description: str

    @abstractmethod
    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        """Evaluate statement and transactions against account tier tariff rules."""
        pass
