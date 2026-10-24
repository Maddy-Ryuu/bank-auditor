"""Test run model for automated audit scenario test suites."""
from sqlalchemy import Column, String, Float, Integer, JSON, DateTime
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, utc_now


class TestRun(UUIDMixin, Base):
    """Tracks audit engine test suite executions, findings discovered, and recovery metrics."""
    __tablename__ = "test_runs"

    test_suite_name = Column(String(100), nullable=False)
    run_type = Column(String(50), nullable=False, default="SYNTHETIC_E2E_AUDIT")
    status = Column(String(20), nullable=False, default="RUNNING")  # SUCCESS, FAILED, RUNNING

    findings_detected_count = Column(Integer, nullable=False, default=0)
    total_fee_amount_audited = Column(Float, nullable=False, default=0.0)
    potential_recovery_amount = Column(Float, nullable=False, default=0.0)
    execution_duration_ms = Column(Integer, nullable=False, default=0)

    details = Column(JSON, nullable=False, default=dict)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
