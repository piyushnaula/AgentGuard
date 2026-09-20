from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentGuard"
    app_env: str = "development"
    database_url: str = "sqlite:///./agentguard.db"
    policy_file: str = "config/policies.yaml"
    log_level: str = "INFO"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    grok_api_key: str = ""
    xai_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_api_key(self) -> str:
        return self.groq_api_key or self.grok_api_key or self.xai_api_key or self.llm_api_key

    @property
    def policy_path(self) -> Path:
        return Path(self.policy_file)


@lru_cache
def get_settings() -> Settings:
    return Settings()
