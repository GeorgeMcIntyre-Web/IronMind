from __future__ import annotations

import functools
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPTIFORGE_", extra="forbid", env_file=".env")

    app_name: str = "OptiForge"
    database_url: str = "sqlite:///data/optiforge.db"
    provider: Literal["openai", "stub"] = "stub"
    provider_model: str = "stub-model"
    provider_base_url: str = "https://api.openai.com"
    provider_api_key: SecretStr | None = None
    log_level: str = "INFO"
    solver_max_seconds: int = 5


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    return settings