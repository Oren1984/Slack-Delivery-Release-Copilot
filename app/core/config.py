from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from environment variables / .env.

    Nothing here enables live external access by default: LLM_MODE defaults to
    "mock" and the Slack adapter never performs network calls regardless of mode.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/copilot.db"
    scenarios_dir: str = "./data/scenarios"

    llm_mode: str = "mock"  # "mock" | "openai_compatible"
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_model: str = ""

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    @property
    def scenarios_path(self) -> Path:
        return Path(self.scenarios_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
