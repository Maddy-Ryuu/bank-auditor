"""Statement and Transaction models."""
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class Statement(UUIDMixin, TimestampMixin, Base):
    """Synthetic monthly or periodic bank statement."""
    __tablename__ = "statements"

    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    statement_period_start = Column(Date, nullable=False)
    statement_period_end = Column(Date, nullable=False)

    opening_balance = Column(Float, nullable=False, default=0.0)
    closing_balance = Column(Float, nullable=False, default=0.0)
    average_daily_balance = Column(Float, nullable=False, default=0.0)
    total_qualifying_direct_deposits = Column(Float, nullable=False, default=0.0)

    # Subsequent statement tracking for refund verification
    is_subsequent_statement = Column(Boolean, nullable=False, default=False)
    verified_against_statement_id = Column(String(36), nullable=True)

    # Immutability and synthetic provenance
    source_id = Column(String(100), nullable=False)
    source_filename = Column(String(150), nullable=False)
    raw_statement_hash = Column(String(64), nullable=False)  # SHA-256

    # Relationships
    account = relationship("Account", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan", order_by="Transaction.transaction_date")
    findings = relationship("AuditFinding", back_populates="statement", cascade="all, delete-orphan")


class Transaction(UUIDMixin, Base):
    """Individual line-item transaction within a statement."""
    __tablename__ = "transactions"

    statement_id = Column(String(36), ForeignKey("statements.id"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # FEE, DEBIT, CREDIT, REFUND, WIRE
    amount = Column(Float, nullable=False)  # Stored as positive float, categorized by transaction_type
    balance_after = Column(Float, nullable=False)
    raw_category = Column(String(50), nullable=False, default="GENERAL")
    source_transaction_id = Column(String(100), nullable=False, index=True)

    # Relationships
    statement = relationship("Statement", back_populates="transactions")
    audit_findings = relationship("AuditFinding", back_populates="transaction")
