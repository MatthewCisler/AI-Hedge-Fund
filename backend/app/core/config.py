"""Application settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed app settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Paper Hedge Fund Simulator"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/paper_hedge_fund"
    )
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_api_key: str = "paper-key"
    alpaca_api_secret: str = "paper-secret"

    local_ai_provider: str = "stub-local-llm"
    market_timezone: str = "America/Chicago"
    market_open_hour_ct: int = 8
    market_open_minute_ct: int = 30
    market_close_hour_ct: int = 15
    market_close_minute_ct: int = 0
    daily_report_hour_ct: int = 15
    daily_report_minute_ct: int = 10


settings = Settings()
