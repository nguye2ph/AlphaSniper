"""Application settings — JSON file persistence for runtime config."""

import json
from pathlib import Path

from pydantic import BaseModel

SETTINGS_FILE = Path("data/settings.json")


class AppSettings(BaseModel):
    watchlist: list[str] = ["AAPL", "TSLA", "MSFT", "NVDA", "AMD"]
    alert_sentiment_threshold: float = 0.5
    alert_enabled: bool = True


def load_settings() -> AppSettings:
    """Load settings from JSON file. Returns defaults if missing."""
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text())
            return AppSettings(**data)
        except (json.JSONDecodeError, Exception):
            pass
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    """Save settings to JSON file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(settings.model_dump_json(indent=2))
