"""OpenInsider HTML scraper — collects insider buy/sell transactions."""

from datetime import datetime, timezone

import httpx
import structlog
from bs4 import BeautifulSoup

from src.collectors.base_collector import BaseCollector
from src.core.models.raw_insider_trade import RawInsiderTrade

logger = structlog.get_logger()

OPENINSIDER_URL = "https://openinsider.com/screener"
# Default params: recent cluster buys (high signal for small-caps)
DEFAULT_PARAMS = {
    "s": "",
    "o": "",
    "pl": "",
    "ph": "",
    "st": "0",
    "ex": "us",
    "t": "cb",  # cluster buys
    "fdlyl": "",
    "fdlyh": "",
    "dtefrom": "",
    "dteto": "",
    "vtefrom": "",
    "vteto": "",
    "tefrom": "",
    "teto": "",
    "cnt": "100",
    "page": "1",
}


class OpenInsiderScraper(BaseCollector):
    """Scrapes OpenInsider for recent insider transactions."""

    source_name = "openinsider"

    async def collect(self) -> None:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "AlphaSniper/1.0 (stock research tool)"},
        ) as client:
            await self._scrape_trades(client)

    async def _scrape_trades(self, client: httpx.AsyncClient) -> int:
        """Scrape the OpenInsider screener page. Returns saved count."""
        try:
            resp = await client.get(OPENINSIDER_URL, params=DEFAULT_PARAMS)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("openinsider_http_error", status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("openinsider_request_error", error=str(e)[:100])
            return 0

        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", class_="tinytable")
        if not table:
            logger.warning("openinsider_no_table")
            return 0

        rows = table.find_all("tr")[1:]  # skip header
        saved = 0

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 12:
                continue

            try:
                filing_date = cols[1].get_text(strip=True)
                ticker = cols[3].get_text(strip=True).upper()
                officer_name = cols[4].get_text(strip=True)
                officer_title = cols[5].get_text(strip=True)
                transaction_type = cols[6].get_text(strip=True)
                price = cols[8].get_text(strip=True)
                shares = cols[9].get_text(strip=True)
                value = cols[10].get_text(strip=True)

                if not ticker or not filing_date:
                    continue

                source_id = f"{ticker}_{filing_date}_{officer_name[:20]}"
                payload = {
                    "filing_date": filing_date,
                    "ticker": ticker,
                    "officer_name": officer_name,
                    "officer_title": officer_title,
                    "transaction_type": transaction_type,
                    "price": price,
                    "shares": shares,
                    "value": value,
                }

                # Dedup check in MongoDB
                existing = await RawInsiderTrade.find_one(
                    RawInsiderTrade.source == self.source_name,
                    RawInsiderTrade.source_id == source_id,
                )
                if existing:
                    continue

                doc = RawInsiderTrade(
                    source=self.source_name,
                    source_id=source_id,
                    payload=payload,
                    collected_at=datetime.now(timezone.utc),
                )
                await doc.insert()
                saved += 1

            except Exception as e:
                logger.debug("openinsider_row_parse_error", error=str(e)[:80])
                continue

        logger.info("openinsider_scraped", rows=len(rows), saved=saved)
        return saved
