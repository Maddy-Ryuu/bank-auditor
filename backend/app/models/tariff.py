"""Tariff rule database model."""
from sqlalchemy import Column, String, Float, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class TariffRule(UUIDMixin, TimestampMixin, Base):
    """Specific fee tariff rule applied to an account tier."""
    __tablename__ = "tariff_rules"

    tier_id = Column(String(36), ForeignKey("account_tiers.id"), nullable=False, index=True)
    fee_category = Column(String(50), nullable=False, index=True)
    fee_name = Column(String(100), nullable=False)
    standard_amount = Column(Float, nullable=False)

    # Detailed rule conditions stored as JSON
    # e.g., {"waiver_type": "min_balance", "threshold": 1500.0, "grace_period_days": 1}
    condition_logic = Column(JSON, nullable=False, default=dict)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    source_document_ref = Column(String(200), nullable=False, default="Schedule of Fees and Charges v2.4")

    # Relationships
    tier = relationship("AccountTier", back_populates="tariff_rules")
    findings = relationship("AuditFinding", back_populates="tariff_rule")
