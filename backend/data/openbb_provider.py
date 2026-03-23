"""
OpenBB-powered data provider — fetches real crypto market data.

Uses yfinance under the hood (same engine OpenBB wraps for free data).
Provides:
- Real-time crypto prices (BTC, ETH, SOL, BNB, XRP, DOGE, etc.)
- Historical OHLCV data for backtesting and strategy signals
- Technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Price change calculations

This replaces the MarketSimulator's synthetic data with real market data.
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

import pandas as pd
import yfinance as yf
import ta
from loguru import logger


# ─── Symbol Mapping ─────────────────────────────────────────────

# Map our internal market IDs to Yahoo Finance tickers
CRYPTO_SYMBOLS = {
    # Binance spot markets
    "bin-btc-usdt": {"yf": "BTC-USD", "name": "BTC/USDT", "symbol": "BTC/USDT", "platform": "binance", "type": "spot"},
    "bin-eth-usdt": {"yf": "ETH-USD", "name": "ETH/USDT", "symbol": "ETH/USDT", "platform": "binance", "type": "spot"},
    "bin-sol-usdt": {"yf": "SOL-USD", "name": "SOL/USDT", "symbol": "SOL/USDT", "platform": "binance", "type": "spot"},
    "bin-bnb-usdt": {"yf": "BNB-USD", "name": "BNB/USDT", "symbol": "BNB/USDT", "platform": "binance", "type": "spot"},
    "bin-xrp-usdt": {"yf": "XRP-USD", "name": "XRP/USDT", "symbol": "XRP/USDT", "platform": "binance", "type": "spot"},
    "bin-doge-usdt": {"yf": "DOGE-USD", "name": "DOGE/USDT", "symbol": "DOGE/USDT", "platform": "binance", "type": "spot"},
    # Hyperliquid perp markets (use same price source, add perp metadata)
    "hl-btc-perp": {"yf": "BTC-USD", "name": "BTC-PERP", "symbol": "BTC-PERP", "platform": "hyperliquid", "type": "perp"},
    "hl-eth-perp": {"yf": "ETH-USD", "name": "ETH-PERP", "symbol": "ETH-PERP", "platform": "hyperliquid", "type": "perp"},
    "hl-sol-perp": {"yf": "SOL-USD", "name": "SOL-PERP", "symbol": "SOL-PERP", "platform": "hyperliquid", "type": "perp"},
    "hl-arb-perp": {"yf": "ARB11841-USD", "name": "ARB-PERP", "symbol": "ARB-PERP", "platform": "hyperliquid", "type": "perp"},
    "hl-wif-perp": {"yf": "WIF-USD", "name": "WIF-PERP", "symbol": "WIF-PERP", "platform": "hyperliquid", "type": "perp"},
}

# Perp-specific metadata (simulated since we don't have real Hyperliquid data)
PERP_META = {
    "hl-btc-perp": {"funding_rate": 0.0001, "open_interest": 850_000_000, "leverage_max": 50},
    "hl-eth-perp": {"funding_rate": 0.00008, "open_interest": 420_000_000, "leverage_max": 50},
    "hl-sol-perp": {"funding_rate": 0.00012, "open_interest": 180_000_000, "leverage_max": 20},
    "hl-arb-perp": {"funding_rate": -0.00005, "open_interest": 45_000_000, "leverage_max": 20},
    "hl-wif-perp": {"funding_rate": 0.0003, "open_interest": 25_000_000, "leverage_max": 10},
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


class OpenBBDataProvider:
    """
    Real market data provider using yfinance (OpenBB's free data engine).

    Fetches real crypto prices, caches them, and provides the same interface
    as the MarketSimulator so it can be swapped in seamlessly.
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
            logger.info("OpenBB data provider started")

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
        """Fetch current prices for all tracked symbols."""
        # Deduplicate yf tickers
        yf_tickers = list(set(s["yf"] for s in CRYPTO_SYMBOLS.values()))
        ticker_str = " ".join(yf_tickers)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._download_prices, ticker_str)

            if data is None or data.empty:
                logger.warning("Empty price data from yfinance")
                return

            now = time.time()

            for market_id, meta in CRYPTO_SYMBOLS.items():
                yf_ticker = meta["yf"]
                try:
                    if len(yf_tickers) == 1:
                        row = data.iloc[-1]
                    else:
                        # Multi-ticker: columns are multi-indexed
                        if yf_ticker not in data.columns.get_level_values(1):
                            continue
                        row = data.xs(yf_ticker, level=1, axis=1).iloc[-1]

                    price = float(row.get("Close", 0))
                    high = float(row.get("High", price))
                    low = float(row.get("Low", price))
                    volume = float(row.get("Volume", 0))

                    if price <= 0:
                        continue

                    # Calculate 24h change
                    prev_close = float(row.get("Open", price))
                    change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

                    # Simulate bid/ask spread (tight for major crypto)
                    spread_pct = 0.0005  # 0.05% spread
                    spread = price * spread_pct

                    self._prices[market_id] = CachedPrice(
                        price=price,
                        bid=round(price - spread / 2, 2),
                        ask=round(price + spread / 2, 2),
                        change_24h=round(change_pct, 2),
                        volume_24h=volume * price,  # Convert to USD volume
                        high_24h=high,
                        low_24h=low,
                        updated_at=now,
                    )
                except Exception as e:
                    logger.debug(f"Error parsing {market_id}: {e}")

            self._last_fetch = now
            logger.debug(f"Updated {len(self._prices)} crypto prices")

        except Exception as e:
            logger.error(f"yfinance download error: {e}")

    def _download_prices(self, ticker_str: str):
        """Synchronous yfinance download (called in executor)."""
        return yf.download(ticker_str, period="2d", interval="1h", progress=False, auto_adjust=True)

    async def _fetch_all_historical(self):
        """Fetch 90 days of daily OHLCV data for strategy calculations."""
        for market_id, meta in CRYPTO_SYMBOLS.items():
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
        """Compute technical indicators for a market's historical data."""
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

    # ─── Public API (matches MarketSimulator interface) ──────

    def get_markets(self, platform: str = "", search: str = "", limit: int = 50) -> list[dict]:
        """Get all markets with real price data."""
        results = []
        for market_id, meta in CRYPTO_SYMBOLS.items():
            if platform and meta["platform"] != platform:
                continue
            if search and search.lower() not in meta["name"].lower() and search.lower() not in meta["symbol"].lower():
                continue

            cached = self._prices.get(market_id)
            if not cached:
                continue

            d = {
                "id": market_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "platform": meta["platform"],
                "marketType": meta["type"],
                "description": f"{meta['name']} — real market data",
                "price": round(cached.price, 2),
                "change": round(cached.change_24h / 100, 4),  # As fraction
                "volume": _format_volume(cached.volume_24h),
                "category": "crypto",
                "active": True,
                "dataSource": "live",
                "high24h": round(cached.high_24h, 2),
                "low24h": round(cached.low_24h, 2),
            }

            if meta["type"] == "perp":
                pm = PERP_META.get(market_id, {})
                d["fundingRate"] = round(pm.get("funding_rate", 0) + random.gauss(0, 0.00002), 6)
                d["openInterest"] = _format_volume(pm.get("open_interest", 0))
                d["leverageMax"] = pm.get("leverage_max", 1)

            results.append(d)

        return results[:limit]

    def get_market(self, market_id: str) -> Optional[dict]:
        """Get a single market."""
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
        step = cached.price * 0.001  # 0.1% per level

        for i in range(8):
            bid_price = round(cached.bid - i * step, 2)
            ask_price = round(cached.ask + i * step, 2)
            bid_size = round(random.uniform(0.1, 5.0) * (1 + i * 0.3), 4)
            ask_size = round(random.uniform(0.1, 5.0) * (1 + i * 0.3), 4)
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
                "price": round(float(val), 2),
            })
        return result

    def get_indicators(self, market_id: str) -> dict:
        """Get latest technical indicators for a market."""
        return self._indicators.get(market_id, {})

    def get_historical_df(self, market_id: str) -> Optional[pd.DataFrame]:
        """Get raw historical DataFrame for strategy use."""
        return self._historical.get(market_id)

    def get_all_indicators(self) -> dict[str, dict]:
        """Get indicators for all markets."""
        return dict(self._indicators)

    async def refresh_historical(self):
        """Force refresh historical data and recompute indicators."""
        await self._fetch_all_historical()
