"""Base models and mixins."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from backend.app.database import Base


def generate_uuid() -> str:
    """Generate a stable standard string UUIDv4."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class UUIDMixin:
    """Mixin for stable primary key UUIDs."""
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        index=True
    )


class TimestampMixin:
    """Mixin for tracking creation and modification timestamps."""
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
