from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# cashflow/src/cashflow/utils/config.py → repository root (editable install via `uv sync`)
REPO_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CASHFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Deployment configuration (environment)
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    connectors_dir: Path = REPO_DIR / "connectors"
    data_dir: Path = Path.home() / ".local" / "share" / "cashflow"

    # Fixed defaults
    max_upload_mb: ClassVar[int] = 20
    max_previews: ClassVar[int] = 20  # import previews kept in memory until committed

    @property
    def database_path(self) -> Path:
        return self.data_dir / "cashflow.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
