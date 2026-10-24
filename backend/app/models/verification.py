"""Verification result database model."""
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class VerificationResult(UUIDMixin, TimestampMixin, Base):
    """Tracks reconciliation of refunds on subsequent bank statements."""
    __tablename__ = "verification_results"

    reversal_request_id = Column(String(36), ForeignKey("reversal_requests.id"), nullable=False, index=True)
    subsequent_statement_id = Column(String(36), ForeignKey("statements.id"), nullable=False, index=True)
    refund_transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True, index=True)

    is_verified = Column(Boolean, nullable=False, default=False)
    verified_amount = Column(Float, nullable=False, default=0.0)
    expected_amount = Column(Float, nullable=False, default=0.0)
    discrepancy_amount = Column(Float, nullable=False, default=0.0)

    verification_status = Column(
        String(40),
        nullable=False,
        default="PENDING_STATEMENT"
    )  # MATCHED_EXACT, PARTIAL_REFUND, NOT_FOUND_IN_SUBSEQUENT, PENDING_STATEMENT

    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    reversal_request = relationship("ReversalRequest", back_populates="verification_results")
