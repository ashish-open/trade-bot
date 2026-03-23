"""
Real forex (FX) data provider using yfinance.

Provides:
- Real-time forex pair prices (EUR/USD, GBP/USD, JPY/USD, etc.)
- Historical OHLCV data for backtesting
- Technical indicators (SMA, RSI, MACD, Bollinger Bands)
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

import pandas as pd
import yfinance as yf
import ta
from loguru import logger


# ─── Symbol Mapping ─────────────────────────────────────────────

# Map internal market IDs to Yahoo Finance tickers (using =X suffix for forex)
FOREX_SYMBOLS = {
    "fx-EUR-USD": {"yf": "EURUSD=X", "name": "Euro / US Dollar", "symbol": "EUR/USD", "base": "EUR", "quote": "USD"},
    "fx-GBP-USD": {"yf": "GBPUSD=X", "name": "British Pound / US Dollar", "symbol": "GBP/USD", "base": "GBP", "quote": "USD"},
    "fx-USD-JPY": {"yf": "USDJPY=X", "name": "US Dollar / Japanese Yen", "symbol": "USD/JPY", "base": "USD", "quote": "JPY"},
    "fx-USD-CHF": {"yf": "USDCHF=X", "name": "US Dollar / Swiss Franc", "symbol": "USD/CHF", "base": "USD", "quote": "CHF"},
    "fx-AUD-USD": {"yf": "AUDUSD=X", "name": "Australian Dollar / US Dollar", "symbol": "AUD/USD", "base": "AUD", "quote": "USD"},
    "fx-NZD-USD": {"yf": "NZDUSD=X", "name": "New Zealand Dollar / US Dollar", "symbol": "NZD/USD", "base": "NZD", "quote": "USD"},
    "fx-USD-CAD": {"yf": "USDCAD=X", "name": "US Dollar / Canadian Dollar", "symbol": "USD/CAD", "base": "USD", "quote": "CAD"},
    "fx-EUR-GBP": {"yf": "EURGBP=X", "name": "Euro / British Pound", "symbol": "EUR/GBP", "base": "EUR", "quote": "GBP"},
    "fx-EUR-JPY": {"yf": "EURJPY=X", "name": "Euro / Japanese Yen", "symbol": "EUR/JPY", "base": "EUR", "quote": "JPY"},
    "fx-GBP-JPY": {"yf": "GBPJPY=X", "name": "British Pound / Japanese Yen", "symbol": "GBP/JPY", "base": "GBP", "quote": "JPY"},
}


def _format_volume(vol: float) -> str:
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.1f}B"
    elif vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    else:
        return f"${vol / 1_000:.0f}K"


@dataclass
class CachedPrice:
    """Holds a cached price with timestamp."""
    price: float
    bid: float
    ask: float
    change_24h: float  # Percentage
    volume_24h: float
    high_24h: float
    low_24h: float
    updated_at: float = field(default_factory=time.time)


class ForexDataProvider:
    """
    Real forex data provider using yfinance.

    Fetches real forex pair prices, caches them, and computes technical indicators
    for currency trading strategies.
    """

    def __init__(self, refresh_interval: float = 30.0):
        self.refresh_interval = refresh_interval
        self._prices: dict[str, CachedPrice] = {}
        self._historical: dict[str, pd.DataFrame] = {}  # market_id -> OHLCV DataFrame
        self._indicators: dict[str, dict] = {}  # market_id -> latest indicator values
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_fetch: float = 0

    # ─── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the background price refresh loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._refresh_loop())
            logger.info("Forex data provider started")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def is_running(self) -> bool:
        return self._running and len(self._prices) > 0

    async def _refresh_loop(self):
        """Periodically fetch latest prices from Yahoo Finance."""
        # Initial fetch
        await self._fetch_all_prices()
        await self._fetch_all_historical()

        while self._running:
            await asyncio.sleep(self.refresh_interval)
            try:
                await self._fetch_all_prices()
            except Exception as e:
                logger.error(f"Price refresh error: {e}")

    async def _fetch_all_prices(self):
        """Fetch current prices for all tracked forex pairs individually."""
        loop = asyncio.get_event_loop()
        now = time.time()

        for market_id, meta in FOREX_SYMBOLS.items():
            try:
                result = await loop.run_in_executor(None, self._fetch_single_pair, meta["yf"])
                if result:
                    price, high, low, volume, change_pct = result

                    spread_pct = 0.0002
                    spread = price * spread_pct

                    self._prices[market_id] = CachedPrice(
                        price=price,
                        bid=round(price - spread / 2, 5),
                        ask=round(price + spread / 2, 5),
                        change_24h=round(change_pct, 2),
                        volume_24h=volume,
                        high_24h=high,
                        low_24h=low,
                        updated_at=now,
                    )
            except Exception as e:
                logger.debug(f"Error fetching {market_id}: {e}")

        self._last_fetch = now
        logger.debug(f"Updated {len(self._prices)} forex prices")

    def _fetch_single_pair(self, yf_ticker: str):
        """Fetch a single forex pair using yf.Ticker (more reliable for =X tickers)."""
        try:
            ticker = yf.Ticker(yf_ticker)
            hist = ticker.history(period="5d")
            if hist is None or hist.empty:
                return None

            price = float(hist["Close"].iloc[-1])
            high = float(hist["High"].iloc[-1])
            low = float(hist["Low"].iloc[-1])
            volume = float(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

            if price <= 0:
                return None

            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else float(hist["Open"].iloc[-1])
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            return (price, high, low, volume, change_pct)
        except Exception:
            return None

    async def _fetch_all_historical(self):
        """Fetch 90 days of daily OHLCV data for strategy calculations."""
        for market_id, meta in FOREX_SYMBOLS.items():
            try:
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(
                    None,
                    lambda t=meta["yf"]: yf.download(t, period="90d", interval="1d", progress=False, auto_adjust=True)
                )
                if df is not None and not df.empty:
                    # Flatten multi-index columns if present
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    self._historical[market_id] = df
                    self._compute_indicators(market_id)
                    logger.debug(f"Loaded {len(df)} days of history for {market_id}")
            except Exception as e:
                logger.debug(f"Historical fetch error for {market_id}: {e}")

    def _compute_indicators(self, market_id: str):
        """Compute technical indicators for a forex pair's historical data."""
        df = self._historical.get(market_id)
        if df is None or len(df) < 30:
            return

        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]

        indicators = {}

        # SMA
        indicators["sma_10"] = float(close.rolling(10).mean().iloc[-1])
        indicators["sma_20"] = float(close.rolling(20).mean().iloc[-1])
        indicators["sma_50"] = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None

        # RSI
        rsi = ta.momentum.RSIIndicator(close, window=14)
        indicators["rsi_14"] = float(rsi.rsi().iloc[-1])

        # MACD
        macd = ta.trend.MACD(close)
        indicators["macd"] = float(macd.macd().iloc[-1])
        indicators["macd_signal"] = float(macd.macd_signal().iloc[-1])
        indicators["macd_histogram"] = float(macd.macd_diff().iloc[-1])

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close)
        indicators["bb_upper"] = float(bb.bollinger_hband().iloc[-1])
        indicators["bb_middle"] = float(bb.bollinger_mavg().iloc[-1])
        indicators["bb_lower"] = float(bb.bollinger_lband().iloc[-1])

        # ATR (Average True Range)
        high = df["High"].squeeze() if isinstance(df["High"], pd.DataFrame) else df["High"]
        low = df["Low"].squeeze() if isinstance(df["Low"], pd.DataFrame) else df["Low"]
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close)
        indicators["atr_14"] = float(atr.average_true_range().iloc[-1])

        indicators["current_price"] = float(close.iloc[-1])
        indicators["updated_at"] = time.time()

        self._indicators[market_id] = indicators

    # ─── Public API ──────────────────────────────────────────

    def get_markets(self, search: str = "", limit: int = 50) -> list[dict]:
        """Get all forex pairs with real price data."""
        results = []
        for market_id, meta in FOREX_SYMBOLS.items():
            if search and search.lower() not in meta["name"].lower() and search.lower() not in meta["symbol"].lower():
                continue

            cached = self._prices.get(market_id)
            if not cached:
                continue

            d = {
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "base": meta["base"],
                "quote": meta["quote"],
                "description": f"{meta['name']} — real market data",
                "price": round(cached.price, 4),
                "change": round(cached.change_24h / 100, 4),  # As fraction
                "volume": _format_volume(cached.volume_24h),
                "category": "forex",
                "active": True,
                "dataSource": "live",
                "high24h": round(cached.high_24h, 4),
                "low24h": round(cached.low_24h, 4),
            }

            results.append(d)

        return results[:limit]

    def get_market(self, market_id: str) -> Optional[dict]:
        """Get a single forex pair."""
        markets = self.get_markets()
        for m in markets:
            if m["id"] == market_id:
                return m
        return None

    def get_price(self, market_id: str, side: str = "buy") -> float:
        """Get current bid or ask price."""
        cached = self._prices.get(market_id)
        if not cached:
            return 0.0
        return cached.ask if side == "buy" else cached.bid

    def get_orderbook(self, market_id: str) -> dict:
        """Generate a realistic order book from cached price data."""
        cached = self._prices.get(market_id)
        if not cached:
            return {"bids": [], "asks": []}

        bids, asks = [], []
        step = cached.price * 0.00001  # 1 pip for forex

        for i in range(8):
            bid_price = round(cached.bid - i * step, 5)
            ask_price = round(cached.ask + i * step, 5)
            bid_size = round(100_000 + i * 50_000, 0)  # Standard forex lot sizes
            ask_size = round(100_000 + i * 50_000, 0)
            if bid_price > 0:
                bids.append({"price": bid_price, "size": bid_size})
            asks.append({"price": ask_price, "size": ask_size})

        return {"bids": bids, "asks": asks}

    def get_price_history(self, market_id: str) -> list[dict]:
        """Get historical OHLCV as list of dicts."""
        df = self._historical.get(market_id)
        if df is None:
            return []

        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
        result = []
        for idx, val in close.items():
            result.append({
                "time": idx.timestamp() if hasattr(idx, 'timestamp') else 0,
                "price": round(float(val), 4),
            })
        return result

    def get_indicators(self, market_id: str) -> dict:
        """Get latest technical indicators for a forex pair."""
        return self._indicators.get(market_id, {})

    def get_historical_df(self, market_id: str) -> Optional[pd.DataFrame]:
        """Get raw historical DataFrame for strategy use."""
        return self._historical.get(market_id)

    def get_all_indicators(self) -> dict[str, dict]:
        """Get indicators for all forex pairs."""
        return dict(self._indicators)

    async def refresh_historical(self):
        """Force refresh historical data and recompute indicators."""
        await self._fetch_all_historical()
