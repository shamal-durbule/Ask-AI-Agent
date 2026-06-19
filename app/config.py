from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://askaiagent:askaiagent@localhost:5432/askaiagent"
    anthropic_api_key: str = ""
    session_storage_path: str = ".sessions"
    log_level: str = "INFO"

    # SQL safety
    max_query_rows: int = 500
    query_timeout_seconds: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
