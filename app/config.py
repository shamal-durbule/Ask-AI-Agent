from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://askaiagent:askaiagent@localhost:5432/askaiagent"
    anthropic_api_key: str = ""
    session_storage_path: str = ".sessions"
    log_level: str = "INFO"
    api_port: int = 8000
    db_port: int = 5432
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # SQL safety
    max_query_rows: int = 500
    query_timeout_seconds: int = 5

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
