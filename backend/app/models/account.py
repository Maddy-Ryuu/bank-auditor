"""Account and Account Tier database models."""
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class AccountTier(UUIDMixin, TimestampMixin, Base):
    """Account Tier defines the official fee schedule and waiver thresholds."""
    __tablename__ = "account_tiers"

    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    # Standard fees and waiver thresholds
    monthly_maintenance_fee = Column(Float, nullable=False, default=12.00)
    min_balance_waiver = Column(Float, nullable=False, default=1500.00)
    min_direct_deposit_waiver = Column(Float, nullable=False, default=500.00)

    # Overdraft policy
    overdraft_fee_amount = Column(Float, nullable=False, default=35.00)
    max_daily_overdraft_fees = Column(Integer, nullable=False, default=3)
    overdraft_threshold_cents = Column(Integer, nullable=False, default=500)  # $5.00 grace limit

    # Wire and paper statement fees
    wire_incoming_domestic_fee = Column(Float, nullable=False, default=0.00)
    wire_outgoing_domestic_fee = Column(Float, nullable=False, default=25.00)
    wire_outgoing_international_fee = Column(Float, nullable=False, default=45.00)
    paper_statement_fee = Column(Float, nullable=False, default=3.00)
    foreign_transaction_fee_rate = Column(Float, nullable=False, default=0.03)  # 3%

    # Relationships
    accounts = relationship("Account", back_populates="tier", cascade="all, delete-orphan")
    tariff_rules = relationship("TariffRule", back_populates="tier", cascade="all, delete-orphan")


class Account(UUIDMixin, TimestampMixin, Base):
    """Bank account owned by the client."""
    __tablename__ = "accounts"

    account_number = Column(String(50), unique=True, nullable=False, index=True)
    holder_name = Column(String(150), nullable=False)
    bank_name = Column(String(100), nullable=False, default="Apex National Bank")
    routing_number = Column(String(20), nullable=False, default="021000021")
    currency = Column(String(3), nullable=False, default="USD")
    current_balance = Column(Float, nullable=False, default=0.0)

    tier_id = Column(String(36), ForeignKey("account_tiers.id"), nullable=False, index=True)
    electronic_statements_enrolled = Column(Boolean, nullable=False, default=True)

    # Source & retrieval metadata
    source_id = Column(String(100), nullable=False, default="SYNTH-ACC-GEN-01")
    source_url = Column(String(255), nullable=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    tier = relationship("AccountTier", back_populates="accounts")
    statements = relationship("Statement", back_populates="account", cascade="all, delete-orphan")
    reversal_requests = relationship("ReversalRequest", back_populates="account")
