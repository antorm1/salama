"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security
    secret_key: str = "dev-insecure-change-me-please-use-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Database (SQLite by default; swap for Postgres in production)
    database_url: str = "sqlite:///./salama.db"

    # App
    app_name: str = "Salama Community Safety"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Seed admin (optional)
    seed_admin_username: str = "admin"
    seed_admin_password: str = "salama-admin-pass"
    seed_admin_phone: str = "+254700000000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
