"""Reversal request, approval audit trail, and mock bank acknowledgement models."""
from sqlalchemy import Column, String, Float, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class ReversalRequest(UUIDMixin, TimestampMixin, Base):
    """Formal fee dispute/reversal request generated from an audit finding."""
    __tablename__ = "reversal_requests"

    finding_id = Column(String(36), ForeignKey("audit_findings.id"), unique=True, nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    reference_number = Column(String(50), unique=True, nullable=False, index=True)
    requested_amount = Column(Float, nullable=False)

    # Formal dispute letter drafted for bank presentation
    rationale_letter = Column(Text, nullable=False)

    status = Column(
        String(40),
        nullable=False,
        default="DRAFTED",
        index=True
    )  # DRAFTED, PENDING_APPROVAL, APPROVED, REJECTED, SUBMITTED_TO_MOCK_PORTAL, ACKNOWLEDGED, SETTLED

    prepared_by = Column(String(100), nullable=False, default="Automated Fee Audit Engine")

    # Relationships
    finding = relationship("AuditFinding", back_populates="reversal_request")
    account = relationship("Account", back_populates="reversal_requests")
    approvals = relationship("ApprovalEvent", back_populates="reversal_request", cascade="all, delete-orphan", order_by="ApprovalEvent.event_timestamp")
    mock_ack = relationship("MockBankAck", back_populates="reversal_request", uselist=False, cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="reversal_request", cascade="all, delete-orphan")


class ApprovalEvent(UUIDMixin, Base):
    """Immutable audit trail log for human-in-the-loop review before mock submission."""
    __tablename__ = "approval_events"

    reversal_request_id = Column(String(36), ForeignKey("reversal_requests.id"), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # APPROVE, REJECT, REQUEST_REVISION
    approved_by_user = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True, default="127.0.0.1")
    event_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    reversal_request = relationship("ReversalRequest", back_populates="approvals")


class MockBankAck(UUIDMixin, Base):
    """Record of mock submission response received from the mock bank portal."""
    __tablename__ = "mock_bank_acks"

    reversal_request_id = Column(String(36), ForeignKey("reversal_requests.id"), unique=True, nullable=False, index=True)
    mock_bank_ticket_id = Column(String(64), nullable=False, index=True)
    status_received = Column(String(50), nullable=False)  # ACCEPTED, PROCESSED, SCHEDULED_FOR_CYCLE_REFUND
    portal_endpoint_called = Column(String(200), nullable=False)
    acknowledgement_payload = Column(JSON, nullable=False, default=dict)
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    reversal_request = relationship("ReversalRequest", back_populates="mock_ack")
