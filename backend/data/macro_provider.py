"""
Macroeconomic and market indices data provider using yfinance.

Provides:
- Global stock market indices (S&P 500, Dow Jones, Nasdaq, etc.)
- Treasury yield curve data (10Y, 5Y, 30Y, 13W)
- Commodity prices (Gold, Silver, Crude Oil, Natural Gas)
- Volatility index (VIX)
- Market overview dashboard
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field

import pandas as pd
import yfinance as yf
from loguru import logger


# ─── Symbol Mapping ─────────────────────────────────────────────

MARKET_INDICES = {
    "idx-sp500": {"yf": "^GSPC", "name": "S&P 500", "symbol": "^GSPC", "category": "US Large Cap"},
    "idx-dow": {"yf": "^DJI", "name": "Dow Jones Industrial Average", "symbol": "^DJI", "category": "US Large Cap"},
    "idx-nasdaq": {"yf": "^IXIC", "name": "Nasdaq Composite", "symbol": "^IXIC", "category": "US Tech"},
    "idx-russell": {"yf": "^RUT", "name": "Russell 2000", "symbol": "^RUT", "category": "US Small Cap"},
    "idx-ftse": {"yf": "^FTSE", "name": "FTSE 100", "symbol": "^FTSE", "category": "UK Large Cap"},
    "idx-dax": {"yf": "^GDAXI", "name": "DAX", "symbol": "^GDAXI", "category": "Germany"},
    "idx-nikkei": {"yf": "^N225", "name": "Nikkei 225", "symbol": "^N225", "category": "Japan"},
    "idx-hangseng": {"yf": "^HSI", "name": "Hang Seng", "symbol": "^HSI", "category": "Hong Kong"},
    "idx-stoxx50": {"yf": "^STOXX50E", "name": "STOXX 50", "symbol": "^STOXX50E", "category": "Eurozone"},
}

TREASURY_YIELDS = {
    "bond-10y": {"yf": "^TNX", "name": "10-Year Treasury Yield", "symbol": "^TNX", "maturity": "10Y"},
    "bond-5y": {"yf": "^FVX", "name": "5-Year Treasury Yield", "symbol": "^FVX", "maturity": "5Y"},
    "bond-30y": {"yf": "^TYX", "name": "30-Year Treasury Yield", "symbol": "^TYX", "maturity": "30Y"},
    "bond-13w": {"yf": "^IRX", "name": "13-Week Treasury Yield", "symbol": "^IRX", "maturity": "13W"},
}

COMMODITIES = {
    "cmd-gold": {"yf": "GC=F", "name": "Gold Futures", "symbol": "GC=F", "unit": "USD/oz"},
    "cmd-silver": {"yf": "SI=F", "name": "Silver Futures", "symbol": "SI=F", "unit": "USD/oz"},
    "cmd-crude": {"yf": "CL=F", "name": "Crude Oil Futures", "symbol": "CL=F", "unit": "USD/bbl"},
    "cmd-natgas": {"yf": "NG=F", "name": "Natural Gas Futures", "symbol": "NG=F", "unit": "USD/MMBtu"},
}

VOLATILITY = {
    "vol-vix": {"yf": "^VIX", "name": "VIX", "symbol": "^VIX", "description": "S&P 500 Volatility Index"},
}


def _format_value(val: float) -> str:
    """Format a generic value."""
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f}B"
    elif val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    else:
        return f"{val:.2f}"


@dataclass
class CachedPrice:
    """Holds a cached price with timestamp."""
    price: float
    change_24h: float  # Percentage
    updated_at: float = field(default_factory=time.time)


class MacroDataProvider:
    """
    Macroeconomic data provider using yfinance.

    Fetches global indices, treasury yields, commodities, and volatility indices.
    Provides market overview dashboard and real-time macro data.
    """

    def __init__(self, refresh_interval: float = 60.0):
        self.refresh_interval = refresh_interval
        self._indices: dict[str, CachedPrice] = {}
        self._yields: dict[str, CachedPrice] = {}
        self._commodities: dict[str, CachedPrice] = {}
        self._volatility: dict[str, CachedPrice] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_fetch: float = 0

    # ─── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the background data refresh loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._refresh_loop())
            logger.info("Macro data provider started")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def is_running(self) -> bool:
        return self._running and (len(self._indices) > 0 or len(self._yields) > 0)

    async def _refresh_loop(self):
        """Periodically fetch latest macro data from Yahoo Finance."""
        # Initial fetch
        await self._fetch_all_data()

        while self._running:
            await asyncio.sleep(self.refresh_interval)
            try:
                await self._fetch_all_data()
            except Exception as e:
                logger.error(f"Macro data refresh error: {e}")

    async def _fetch_all_data(self):
        """Fetch all macro data (indices, yields, commodities, volatility)."""
        await asyncio.gather(
            self._fetch_indices(),
            self._fetch_yields(),
            self._fetch_commodities(),
            self._fetch_volatility(),
        )

    async def _fetch_indices(self):
        """Fetch global market indices."""
        for market_id, meta in MARKET_INDICES.items():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._fetch_single_price, market_id, meta, self._indices)
            except Exception as e:
                logger.debug(f"Indices fetch error for {market_id}: {e}")

    async def _fetch_yields(self):
        """Fetch treasury yields."""
        for market_id, meta in TREASURY_YIELDS.items():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._fetch_single_price, market_id, meta, self._yields)
            except Exception as e:
                logger.debug(f"Yields fetch error for {market_id}: {e}")

    async def _fetch_commodities(self):
        """Fetch commodity prices."""
        for market_id, meta in COMMODITIES.items():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._fetch_single_price, market_id, meta, self._commodities)
            except Exception as e:
                logger.debug(f"Commodities fetch error for {market_id}: {e}")

    async def _fetch_volatility(self):
        """Fetch volatility indices."""
        for market_id, meta in VOLATILITY.items():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._fetch_single_price, market_id, meta, self._volatility)
            except Exception as e:
                logger.debug(f"Volatility fetch error for {market_id}: {e}")

    def _fetch_single_price(self, market_id: str, meta: dict, cache: dict):
        """Synchronous price fetch for a single ticker (called in executor)."""
        try:
            yf_ticker = meta["yf"]
            ticker_obj = yf.Ticker(yf_ticker)
            hist = ticker_obj.history(period="5d")

            if hist is None or hist.empty:
                return

            price = float(hist["Close"].iloc[-1])
            if price <= 0:
                return

            # Get previous close for change calc
            if len(hist) >= 2:
                prev_close = float(hist["Close"].iloc[-2])
            else:
                prev_close = float(hist["Open"].iloc[-1])

            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            cache[market_id] = CachedPrice(
                price=price,
                change_24h=round(change_pct, 2),
                updated_at=time.time(),
            )
            logger.debug(f"Updated {market_id}: ${price:.2f} ({change_pct:+.2f}%)")
        except Exception as e:
            logger.debug(f"Error fetching {market_id}: {e}")

    # ─── Public API ──────────────────────────────────────────

    def get_indices(self) -> list[dict]:
        """Get all global market indices."""
        results = []
        for market_id, meta in MARKET_INDICES.items():
            cached = self._indices.get(market_id)
            if not cached:
                continue

            results.append({
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "category": meta["category"],
                "price": round(cached.price, 2),
                "change": round(cached.change_24h, 2),
                "updated_at": cached.updated_at,
            })

        return results

    def get_treasury_yields(self) -> list[dict]:
        """Get treasury yield curve data."""
        results = []
        for market_id, meta in TREASURY_YIELDS.items():
            cached = self._yields.get(market_id)
            if not cached:
                continue

            results.append({
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "maturity": meta["maturity"],
                "yield": round(cached.price, 3),
                "change": round(cached.change_24h, 3),
                "updated_at": cached.updated_at,
            })

        return results

    def get_commodities(self) -> list[dict]:
        """Get commodity prices."""
        results = []
        for market_id, meta in COMMODITIES.items():
            cached = self._commodities.get(market_id)
            if not cached:
                continue

            results.append({
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "unit": meta["unit"],
                "price": round(cached.price, 2),
                "change": round(cached.change_24h, 2),
                "updated_at": cached.updated_at,
            })

        return results

    def get_volatility(self) -> list[dict]:
        """Get volatility indices (VIX, etc.)."""
        results = []
        for market_id, meta in VOLATILITY.items():
            cached = self._volatility.get(market_id)
            if not cached:
                continue

            results.append({
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "description": meta["description"],
                "value": round(cached.price, 2),
                "change": round(cached.change_24h, 2),
                "updated_at": cached.updated_at,
            })

        return results

    def get_index(self, market_id: str) -> Optional[dict]:
        """Get a single index."""
        indices = self.get_indices()
        for idx in indices:
            if idx["id"] == market_id:
                return idx
        return None

    def get_yield(self, market_id: str) -> Optional[dict]:
        """Get a single treasury yield."""
        yields = self.get_treasury_yields()
        for y in yields:
            if y["id"] == market_id:
                return y
        return None

    def get_commodity(self, market_id: str) -> Optional[dict]:
        """Get a single commodity."""
        commodities = self.get_commodities()
        for c in commodities:
            if c["id"] == market_id:
                return c
        return None

    def get_vix(self) -> Optional[dict]:
        """Get VIX (S&P 500 volatility index)."""
        volatility = self.get_volatility()
        for v in volatility:
            if v["id"] == "vol-vix":
                return v
        return None

    def get_overview(self) -> dict:
        """
        Get a comprehensive market overview dashboard.

        Returns a dict with sections for indices, bonds, commodities, and volatility.
        """
        sp500 = self.get_index("idx-sp500")
        dow = self.get_index("idx-dow")
        nasdaq = self.get_index("idx-nasdaq")
        vix = self.get_vix()
        yields = self.get_treasury_yields()
        commodities = self.get_commodities()

        # Determine market sentiment
        sentiment = "neutral"
        if sp500 and sp500["change"] > 1.0:
            sentiment = "bullish"
        elif sp500 and sp500["change"] < -1.0:
            sentiment = "bearish"

        return {
            "timestamp": time.time(),
            "sentiment": sentiment,
            "indices": {
                "sp500": sp500 or {},
                "dow": dow or {},
                "nasdaq": nasdaq or {},
                "all": self.get_indices(),
            },
            "bonds": {
                "yields": yields,
                "yield_curve": self._compute_yield_curve(yields),
            },
            "commodities": {
                "all": commodities,
                "gold": next((c for c in commodities if c["id"] == "cmd-gold"), None),
                "crude": next((c for c in commodities if c["id"] == "cmd-crude"), None),
            },
            "volatility": {
                "vix": vix or {},
                "market_condition": self._assess_market_condition(vix),
            },
        }

    def _compute_yield_curve(self, yields: list[dict]) -> dict:
        """Compute yield curve inversion indicators."""
        if len(yields) < 2:
            return {}

        # Find 10Y and 2Y (or 5Y as proxy) yields
        ten_y = next((y for y in yields if y["maturity"] == "10Y"), None)
        five_y = next((y for y in yields if y["maturity"] == "5Y"), None)

        if not (ten_y and five_y):
            return {}

        spread = ten_y["yield"] - five_y["yield"]
        is_inverted = spread < 0

        return {
            "spread_10y_5y": round(spread, 3),
            "is_inverted": is_inverted,
            "level": "inverted" if is_inverted else "normal",
        }

    def _assess_market_condition(self, vix: Optional[dict]) -> str:
        """Assess market volatility condition based on VIX."""
        if not vix:
            return "unknown"

        vix_level = vix.get("value", 0)
        if vix_level < 12:
            return "very_low_volatility"
        elif vix_level < 20:
            return "low_volatility"
        elif vix_level < 30:
            return "normal_volatility"
        elif vix_level < 40:
            return "elevated_volatility"
        else:
            return "extreme_volatility"

    async def refresh_all(self):
        """Force refresh all macro data."""
        await self._fetch_all_data()
