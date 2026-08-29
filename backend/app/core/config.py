"""Application configuration, loaded from environment variables.

Uses pydantic-settings so config is validated at startup and can be
overridden via a local .env file (see .env.example) without code changes.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Football Odds Service backend."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # General
    app_env: str = "development"  # development | production
    service_name: str = "football-odds-service"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS: origins allowed to call this API (comma-separated in .env)
    frontend_origin: str = "http://localhost:3000"


# Single shared settings instance, imported wherever config is needed.
settings = Settings()
