"""Redis-backed market cap cache with Finnhub /stock/profile2 lookup."""

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

FINNHUB_PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"
CACHE_TTL = 86400  # 24 hours
CACHE_PREFIX = "mcap:"


class MarketCapCache:
    """Lookup and cache market capitalization per ticker via Finnhub API."""

    def __init__(self, redis_client, api_key: str, limit: int = 100_000_000):
        self.redis = redis_client
        self.api_key = api_key
        self.limit = limit

    async def get_market_cap(self, ticker: str) -> float | None:
        """Get market cap for ticker. Returns USD value or None if unknown."""
        cache_key = f"{CACHE_PREFIX}{ticker.upper()}"

        # Check cache first
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return float(cached) if cached != "null" else None

        # Cache miss — fetch from Finnhub
        mc = await self._fetch_from_finnhub(ticker)

        # Cache result (even None as "null" to avoid repeated API calls)
        await self.redis.set(cache_key, str(mc) if mc is not None else "null", ex=CACHE_TTL)
        return mc

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5), reraise=False)
    async def _fetch_from_finnhub(self, ticker: str) -> float | None:
        """Fetch market cap from Finnhub /stock/profile2 endpoint.
        Returns market cap in USD (response gives millions, we convert)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    FINNHUB_PROFILE_URL,
                    params={"symbol": ticker.upper(), "token": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                # marketCapitalization is in millions
                mc_millions = data.get("marketCapitalization")
                if mc_millions and mc_millions > 0:
                    return mc_millions * 1_000_000  # Convert to USD
                return None
        except Exception as e:
            logger.warning("mcap_fetch_error", ticker=ticker, error=str(e)[:80])
            return None

    async def is_within_limit(self, market_cap: float | None) -> bool:
        """Check if market cap is within configured limit. None = unknown = keep."""
        if market_cap is None:
            return True
        return market_cap <= self.limit

    async def are_tickers_within_limit(self, tickers: list[str]) -> bool:
        """Check if ANY ticker in list is within limit. Empty list = keep."""
        if not tickers:
            return True
        for ticker in tickers:
            mc = await self.get_market_cap(ticker)
            if await self.is_within_limit(mc):
                return True
        return False
