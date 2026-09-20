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
    def effective_database_url(self) -> str:
        # In Vercel or serverless environments, the root filesystem is read-only.
        # Direct SQLite to /tmp unless an external database (Postgres, etc.) is configured.
        import os

        is_serverless = any([
            os.getenv("VERCEL"),
            os.getenv("VERCEL_ENV"),
            os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            os.getenv("LAMBDA_TASK_ROOT"),
            os.getenv("AWS_EXECUTION_ENV"),
        ])
        if is_serverless and self.database_url.startswith("sqlite"):
            if not self.database_url.startswith("sqlite:////tmp/"):
                return "sqlite:////tmp/agentguard.db"
        return self.database_url

    @property
    def policy_path(self) -> Path:
        path = Path(self.policy_file)
        if path.is_absolute() and path.exists():
            return path
        if path.exists():
            return path
        # Fallback relative to project root
        candidate = Path(__file__).resolve().parent.parent.parent / self.policy_file
        if candidate.exists():
            return candidate
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
