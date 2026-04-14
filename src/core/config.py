"""Application configuration via pydantic-settings. All secrets loaded from .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for AlphaSniper pipeline."""

    # MongoDB (raw zone)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "alpha_sniper"

    # PostgreSQL (clean zone)
    postgres_url: str = "postgresql+asyncpg://alpha:alpha_dev_only@localhost:5432/alpha_sniper"

    # Redis (queue + cache + dedup)
    redis_url: str = "redis://localhost:6379/0"

    # Finnhub (primary data source)
    finnhub_api_key: str = ""
    finnhub_symbols: list[str] = ["AAPL", "TSLA", "MSFT", "NVDA", "AMD"]

    # MarketAux (secondary data source)
    marketaux_api_key: str = ""

    # SEC EDGAR (no key, but needs User-Agent)
    sec_edgar_user_agent: str = "AlphaSniper/1.0 (contact@example.com)"

    # Google Gemini (AI parser - Phase 7)
    gemini_api_key: str = ""

    # Market cap filter (applied to new sources only: TickerTick, Discord)
    market_cap_limit: int = 100_000_000  # 100M USD

    # Discord listener (NuntioBot scraping)
    discord_token: str = ""
    discord_channel_ids: list[str] = []
    nuntio_bot_name: str = "NuntioBot"

    # Discord webhook (outbound alerts)
    discord_webhook_url: str = ""  # Empty = disabled
    discord_sentiment_threshold: float = 0.5

    # Frontend (Vercel URL for CORS)
    frontend_url: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_port: int = 8200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance
settings = Settings()
