"""Application settings via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite+aiosqlite:///./careeros.db",
        description="SQLAlchemy async database URL",
    )
    app_env: Literal["development", "production", "testing"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    secret_key: str = Field(default="change-me", description="Used for internal signing")
    document_storage_path: str = Field(
        default="",
        description="Absolute path for generated document storage (PDFs). Empty = auto.",
    )

    # --- Outreach / SMTP ---
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port (587 for STARTTLS)")
    smtp_sender: str = Field(
        default="", description="From: address — GMAIL_SENDER env or explicit value"
    )
    smtp_password: str = Field(
        default="", description="App password — GMAIL_APP_PASSWORD env or explicit value"
    )
    smtp_use_tls: bool = Field(default=True, description="Use STARTTLS (port 587)")

    # --- Outreach rate limits ---
    outreach_daily_cap: int = Field(
        default=20, description="Max emails sent per day (0 = unlimited)"
    )
    outreach_min_interval_seconds: int = Field(
        default=30, description="Minimum seconds between consecutive sends"
    )

    # --- Email finder APIs ---
    hunter_api_key: str = Field(default="", description="Hunter.io API key")
    apollo_api_key: str = Field(default="", description="Apollo.io API key")

    @field_validator("smtp_sender", mode="before")
    @classmethod
    def _fallback_sender(cls, value: str) -> str:
        if value:
            return value
        import os

        return os.environ.get("GMAIL_SENDER", os.environ.get("SMTP_SENDER", ""))

    @field_validator("smtp_password", mode="before")
    @classmethod
    def _fallback_password(cls, value: str) -> str:
        if value:
            return value
        import os

        return os.environ.get("GMAIL_APP_PASSWORD", os.environ.get("SMTP_PASSWORD", ""))

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def debug(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
