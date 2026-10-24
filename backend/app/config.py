"""Application configuration settings."""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bank Fee Auditor"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    # Supports both PostgreSQL async (postgresql+asyncpg://...) and SQLite async (sqlite+aiosqlite://...)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./bank_fee_auditor.db",
        description="Async database connection string"
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./bank_fee_auditor.db",
        description="Synchronous database connection string for Alembic"
    )

    # Mock Bank Portal
    MOCK_BANK_API_KEY: str = "mock-bank-live-secret-key-audit-portal"
    MOCK_BANK_PORTAL_NAME: str = "Apex National Mock Gateway"
    MOCK_BANK_AUTO_ACK: bool = True
    MOCK_BANK_ACK_LATENCY_MS: int = 150

    # Security & CORS
    SECRET_KEY: str = "audit-system-secret-key-local-only-replace-in-prod"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"

    # Audit Engine Defaults
    AUDIT_FLAG_SEVERITY_DEFAULT: str = "HIGH"
    MAX_DAILY_OVERDRAFT_LIMIT: int = 3
    AUDIT_TOLERANCE_CENTS: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
