"""Application configuration loaded from environment / .env file."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration. Mirrors `.env.example`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = ""
    mock_llm: bool = False

    # App
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 5173
    database_url: str = "sqlite:///./datalens.db"
    max_upload_size_mb: int = 500
    max_query_rows: int = 5000
    max_tool_iterations: int = 4

    # Dev
    debug: bool = False
    cors_origins: str = "http://localhost:5173"

    @property
    def db_path(self) -> Path:
        """Strip the sqlite:/// prefix and return a Path."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return Path(url.removeprefix("sqlite:///"))
        return Path(url)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


_settings: Settings | None = None


def get_settings() -> Settings:
    """Cached settings accessor."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings_for_tests() -> None:
    """Force a re-read of settings — used inside pytest fixtures."""
    global _settings
    _settings = None
