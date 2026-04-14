"""SEC EDGAR collector — 8-K RSS feed parser + company submissions API."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

EDGAR_BASE = "https://data.sec.gov"
EDGAR_RSS = "https://www.sec.gov/cgi-bin/browse-edgar"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Cache directory for ticker lookup
CACHE_DIR = Path(__file__).parent.parent.parent / "data"


class SecEdgarCollector(BaseCollector):
    """Collects 8-K filings and press releases from SEC EDGAR."""

    source_name = "sec_edgar"

    def __init__(self):
        self.user_agent = settings.sec_edgar_user_agent
        self.headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        self._ticker_map: dict[str, str] = {}  # CIK -> ticker

    async def collect(self) -> None:
        """Single poll cycle: fetch latest 8-K filings via RSS."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            await self._ensure_ticker_map(client)
            await self._fetch_8k_filings(client)

    async def _ensure_ticker_map(self, client: httpx.AsyncClient) -> None:
        """Load or refresh CIK-to-ticker mapping from SEC."""
        if self._ticker_map:
            return

        cache_file = CACHE_DIR / "company_tickers.json"

        # Try cache first
        if cache_file.exists():
            try:
                raw = json.loads(cache_file.read_text())
                self._ticker_map = {str(v["cik_str"]): v["ticker"] for v in raw.values()}
                logger.info("ticker_map_loaded_cache", count=len(self._ticker_map))
                return
            except (json.JSONDecodeError, KeyError):
                pass

        # Fetch from SEC
        try:
            resp = await client.get(TICKERS_URL)
            resp.raise_for_status()
            raw = resp.json()
            self._ticker_map = {str(v["cik_str"]): v["ticker"] for v in raw.values()}

            # Cache locally
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(raw))
            logger.info("ticker_map_fetched", count=len(self._ticker_map))
        except Exception as e:
            logger.error("ticker_map_error", error=str(e))

    def _cik_to_ticker(self, cik: str) -> str | None:
        """Resolve CIK number to ticker symbol."""
        # Strip leading zeros for lookup
        cik_clean = cik.lstrip("0")
        return self._ticker_map.get(cik_clean)

    async def _fetch_8k_filings(self, client: httpx.AsyncClient) -> int:
        """Fetch recent 8-K filings via EDGAR full-text search API."""
        params = {
            "q": '"8-K"',
            "dateRange": "custom",
            "startdt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "enddt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "forms": "8-K",
        }

        try:
            resp = await client.get("https://efts.sec.gov/LATEST/search-index", params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("edgar_search_error", status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("edgar_request_error", error=str(e))
            return 0

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        saved = 0

        for hit in hits:
            source_data = hit.get("_source", {})
            filing_id = hit.get("_id", "")
            if not filing_id:
                continue

            # Resolve CIK to ticker
            cik = str(source_data.get("entity_id", ""))
            ticker = self._cik_to_ticker(cik)

            payload = {
                "filing_id": filing_id,
                "form_type": source_data.get("form_type", "8-K"),
                "entity_name": source_data.get("entity_name", ""),
                "cik": cik,
                "ticker": ticker,
                "filed_at": source_data.get("file_date", ""),
                "description": source_data.get("display_names", []),
            }

            result = await self.save_raw(source_id=filing_id, payload=payload)
            if result:
                saved += 1

            # Respect SEC rate limit: 10 req/sec
            await asyncio.sleep(0.1)

        logger.info("edgar_8k_fetched", hits=len(hits), saved=saved)
        return saved


async def main():
    """Standalone: run one collection cycle."""
    collector = SecEdgarCollector()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


if __name__ == "__main__":
    asyncio.run(main())
