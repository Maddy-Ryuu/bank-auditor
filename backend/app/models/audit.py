"""Audit finding model."""
from sqlalchemy import Column, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class AuditFinding(UUIDMixin, TimestampMixin, Base):
    """Audit finding representing a suspicious or non-compliant fee."""
    __tablename__ = "audit_findings"

    statement_id = Column(String(36), ForeignKey("statements.id"), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True, index=True)
    rule_id = Column(String(36), ForeignKey("tariff_rules.id"), nullable=True, index=True)

    rule_category = Column(String(50), nullable=False, index=True)
    fee_amount = Column(Float, nullable=False)
    potential_refund_amount = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False, default="HIGH")  # HIGH, MEDIUM, LOW

    status = Column(
        String(30),
        nullable=False,
        default="FLAGGED",
        index=True
    )  # FLAGGED, REVERSAL_REQUESTED, APPROVED, SUBMITTED, REVERSED, DISMISSED

    violation_title = Column(String(200), nullable=False)
    violation_reason = Column(String(1000), nullable=False)

    # Detailed structured evidence:
    # {
    #   "rule_applied": "MONTHLY_MAINTENANCE_MIN_BALANCE_WAIVER",
    #   "expected_fee": 0.0,
    #   "actual_fee_charged": 12.0,
    #   "threshold_required": 1500.0,
    #   "client_balance_proven": 1820.50,
    #   "evidence_summary": "Account met minimum daily balance threshold of $1,500.00 throughout cycle."
    # }
    evidence_data = Column(JSON, nullable=False, default=dict)
    source_evidence_snapshot = Column(String(500), nullable=True)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    statement = relationship("Statement", back_populates="findings")
    transaction = relationship("Transaction", back_populates="audit_findings")
    tariff_rule = relationship("TariffRule", back_populates="findings")
    reversal_request = relationship("ReversalRequest", back_populates="finding", uselist=False, cascade="all, delete-orphan")
