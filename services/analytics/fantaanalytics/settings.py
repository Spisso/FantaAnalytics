"""Validated runtime configuration without exposing secrets in diagnostics."""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///data/processed/fantaanalytics.db"


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    @classmethod
    def from_env(cls):
        settings = cls(
            database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            api_host=os.getenv("ANALYTICS_API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("ANALYTICS_API_PORT", "8000")),
        )
        settings.validate()
        return settings

    def validate(self):
        if not self.database_url.startswith(("sqlite://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL deve usare sqlite:// o postgresql+psycopg://")
        if not 1 <= self.api_port <= 65535:
            raise ValueError("ANALYTICS_API_PORT non valida")
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL non valido")


def redact_database_url(value):
    if "@" not in value:
        return value
    return f"{value.split('://', 1)[0]}://***@{value.rsplit('@', 1)[1]}"
