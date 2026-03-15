"""App configuration from environment."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Nebius Token Factory (OpenAI-compatible)
    NEBIUS_API_KEY: str = ""
    NEBIUS_BASE_URL: str = "https://api.studio.nebius.com/v1"
    NEBIUS_MODEL: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"

    # Agent schedule (cron or interval)
    AGENT_RUN_CRON: str = "0 6 * * *"  # 6 AM daily
    AGENT_ENABLED: bool = True

    # Simulator
    SIMULATOR_SEED: Optional[int] = None  # fixed seed for reproducible fake data
