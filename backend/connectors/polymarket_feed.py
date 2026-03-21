"""
Polymarket Live Data Feed — fetches real market data from public APIs.

Uses:
- Gamma API (https://gamma-api.polymarket.com) — market discovery, metadata
- CLOB API (https://clob.polymarket.com) — orderbooks, prices, live data

No authentication required for read-only market data.
"""

import asyncio
import httpx
from typing import Optional
from loguru import logger
from datetime import datetime


# ─── API Constants ──────────────────────────────────────────────

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# Curated high-volume markets to track (we'll also fetch trending)
# These are condition_ids — each market has YES/NO token pairs
DEFAULT_CATEGORIES = ["crypto", "politics", "sports", "science", "pop-culture"]


class PolymarketFeed:
    """
    Fetches real Polymarket data for paper trading.

    Usage:
        feed = PolymarketFeed()
        await feed.start()            # Begin periodic refresh
        markets = feed.get_markets()   # Returns cached market data
        book = await feed.fetch_orderbook(token_id)
    """

    def __init__(self, refresh_interval: int = 15):
        """
        Args:
            refresh_interval: Seconds between market data refreshes (default 15).
                              Polymarket APIs are rate-limited, so don't go below 10.
        """
        self.refresh_interval = refresh_interval
        self._client: Optional[httpx.AsyncClient] = None
        self._markets: dict[str, dict] = {}  # condition_id -> market dict
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background data refresh loop."""
        self._client = httpx.AsyncClient(timeout=15.0)
        self._running = True

        # Do an initial fetch
        await self._refresh_markets()

        # Start background loop
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info(f"Polymarket feed started — {len(self._markets)} markets loaded")

    async def stop(self):
        """Stop the feed and clean up."""
        self._running = False
        if self._task:
            self._task.cancel()
        if self._client:
            await self._client.aclose()
        logger.info("Polymarket feed stopped")

    async def _refresh_loop(self):
        """Periodically refresh market data."""
        while self._running:
            await asyncio.sleep(self.refresh_interval)
            try:
                await self._refresh_markets()
            except Exception as e:
                logger.error(f"Polymarket refresh error: {e}")

    # ─── Data Fetching ──────────────────────────────────────────

    async def _refresh_markets(self):
        """Fetch active markets from the Gamma API."""
        try:
            # Fetch trending/active markets with decent volume
            response = await self._client.get(
                f"{GAMMA_API}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "limit": 30,
                    "order": "volume24hr",
                    "ascending": "false",
                },
            )
            response.raise_for_status()
            raw_markets = response.json()

            for raw in raw_markets:
                cond_id = raw.get("conditionId") or raw.get("id", "")
                if not cond_id:
                    continue

                # Parse prices from outcomePrices (JSON string like "[\"0.85\",\"0.15\"]")
                yes_price = 0.50
                no_price = 0.50
                try:
                    import json
                    prices = json.loads(raw.get("outcomePrices", "[]"))
                    if len(prices) >= 2:
                        yes_price = float(prices[0])
                        no_price = float(prices[1])
                except (json.JSONDecodeError, ValueError, IndexError):
                    pass

                # Parse token IDs for orderbook queries
                clob_token_ids = []
                try:
                    import json
                    clob_token_ids = json.loads(raw.get("clobTokenIds", "[]"))
                except (json.JSONDecodeError, ValueError):
                    pass

                volume_raw = float(raw.get("volume", 0) or 0)
                volume_24h_raw = float(raw.get("volume24hr", 0) or 0)

                # Build our market dict
                market = {
                    "id": f"pm-{cond_id[:12]}",
                    "conditionId": cond_id,
                    "clobTokenIds": clob_token_ids,
                    "name": raw.get("question", "Unknown Market"),
                    "symbol": raw.get("ticker", ""),
                    "platform": "polymarket",
                    "marketType": "prediction",
                    "description": raw.get("description", "")[:200],
                    "price": round(yes_price, 4),
                    "yesPrice": round(yes_price, 4),
                    "noPrice": round(no_price, 4),
                    "change": 0.0,  # Will be calculated from price history
                    "volume": self._format_volume(volume_raw),
                    "volume24h": self._format_volume(volume_24h_raw),
                    "category": raw.get("groupSlug", "general"),
                    "endDate": raw.get("endDateIso", ""),
                    "active": True,
                    "image": raw.get("image", ""),
                    "lastUpdated": datetime.utcnow().isoformat(),
                }

                # Track price change
                old = self._markets.get(cond_id)
                if old and old.get("price", 0) > 0:
                    old_price = old["price"]
                    market["change"] = round((yes_price - old_price) / old_price, 4) if old_price else 0

                self._markets[cond_id] = market

            logger.debug(f"Polymarket: refreshed {len(raw_markets)} markets")

        except httpx.HTTPStatusError as e:
            logger.warning(f"Polymarket API HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Polymarket API request error: {e}")

    async def fetch_orderbook(self, market_id: str) -> dict:
        """
        Fetch a real orderbook from the CLOB API.

        Args:
            market_id: Our internal market ID (pm-xxxx)

        Returns:
            {"bids": [{"price": 0.85, "size": 1200}, ...], "asks": [...]}
        """
        market = self._find_market(market_id)
        if not market or not market.get("clobTokenIds"):
            return {"bids": [], "asks": []}

        # Use the YES token (first token ID)
        token_id = market["clobTokenIds"][0]

        try:
            response = await self._client.get(
                f"{CLOB_API}/book",
                params={"token_id": token_id},
            )
            response.raise_for_status()
            raw = response.json()

            bids = [
                {"price": float(b["price"]), "size": float(b["size"])}
                for b in raw.get("bids", [])[:10]
            ]
            asks = [
                {"price": float(a["price"]), "size": float(a["size"])}
                for a in raw.get("asks", [])[:10]
            ]

            return {"bids": bids, "asks": asks}

        except Exception as e:
            logger.warning(f"Polymarket orderbook error: {e}")
            return {"bids": [], "asks": []}

    # ─── Public Getters ─────────────────────────────────────────

    def get_markets(self, search: str = "", limit: int = 30) -> list[dict]:
        """Get cached markets, optionally filtered."""
        results = []
        for m in self._markets.values():
            if search and search.lower() not in m["name"].lower():
                continue
            results.append(m)

        # Sort by volume (most active first)
        results.sort(key=lambda m: float(m.get("volume", "$0").replace("$", "").replace("B", "e9").replace("M", "e6").replace("K", "e3") or 0), reverse=True)
        return results[:limit]

    def get_market(self, market_id: str) -> Optional[dict]:
        """Get a single market by our internal ID."""
        return self._find_market(market_id)

    def get_price(self, market_id: str, side: str = "buy") -> float:
        """Get current price. Buy = ask (slightly higher), sell = bid (slightly lower)."""
        market = self._find_market(market_id)
        if not market:
            return 0.0
        base = market.get("price", 0.50)
        spread = 0.005
        if side == "sell":
            return round(max(0.01, base - spread), 4)
        else:
            return round(min(0.99, base + spread), 4)

    def is_running(self) -> bool:
        return self._running and len(self._markets) > 0

    # ─── Internal Helpers ───────────────────────────────────────

    def _find_market(self, market_id: str) -> Optional[dict]:
        """Find market by either our ID (pm-xxx) or conditionId."""
        for m in self._markets.values():
            if m["id"] == market_id or m["conditionId"] == market_id:
                return m
        return None

    @staticmethod
    def _format_volume(vol: float) -> str:
        if vol >= 1_000_000_000:
            return f"${vol / 1_000_000_000:.1f}B"
        elif vol >= 1_000_000:
            return f"${vol / 1_000_000:.1f}M"
        elif vol >= 1_000:
            return f"${vol / 1_000:.0f}K"
        else:
            return f"${vol:.0f}"
