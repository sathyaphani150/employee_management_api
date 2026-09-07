"""Application configuration loaded exclusively from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings.

    Values can be supplied by environment variables or by a local ``.env`` file.
    The ``.env`` file is intentionally excluded from source control and images.
    """

    app_name: str = "Employee Management API"
    app_environment: str = "development"
    app_version: str = "1.0.0"
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance for the process lifetime."""

    return Settings()
