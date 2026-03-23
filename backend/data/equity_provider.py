"""
Real stock and ETF data provider using yfinance.

Provides:
- Real-time equity prices (AAPL, MSFT, GOOGL, etc.)
- ETF prices (SPY, QQQ, IWM, etc.)
- Historical OHLCV data for backtesting
- Technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Fundamental data (market cap, P/E ratio, dividend yield, etc.)
- Stock screener with filtering by criteria
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

# Map internal market IDs to Yahoo Finance tickers
EQUITY_SYMBOLS = {
    # Major stocks
    "eq-AAPL": {"yf": "AAPL", "name": "Apple Inc.", "symbol": "AAPL", "type": "stock", "sector": "Technology"},
    "eq-MSFT": {"yf": "MSFT", "name": "Microsoft Corp.", "symbol": "MSFT", "type": "stock", "sector": "Technology"},
    "eq-GOOGL": {"yf": "GOOGL", "name": "Alphabet Inc.", "symbol": "GOOGL", "type": "stock", "sector": "Technology"},
    "eq-AMZN": {"yf": "AMZN", "name": "Amazon.com Inc.", "symbol": "AMZN", "type": "stock", "sector": "Consumer Cyclical"},
    "eq-NVDA": {"yf": "NVDA", "name": "NVIDIA Corp.", "symbol": "NVDA", "type": "stock", "sector": "Technology"},
    "eq-TSLA": {"yf": "TSLA", "name": "Tesla Inc.", "symbol": "TSLA", "type": "stock", "sector": "Automotive"},
    "eq-META": {"yf": "META", "name": "Meta Platforms Inc.", "symbol": "META", "type": "stock", "sector": "Technology"},
    "eq-JPM": {"yf": "JPM", "name": "JPMorgan Chase Co.", "symbol": "JPM", "type": "stock", "sector": "Financial Services"},
    "eq-V": {"yf": "V", "name": "Visa Inc.", "symbol": "V", "type": "stock", "sector": "Financial Services"},
    "eq-WMT": {"yf": "WMT", "name": "Walmart Inc.", "symbol": "WMT", "type": "stock", "sector": "Consumer Defensive"},
    "eq-JNJ": {"yf": "JNJ", "name": "Johnson & Johnson", "symbol": "JNJ", "type": "stock", "sector": "Healthcare"},
    "eq-UNH": {"yf": "UNH", "name": "UnitedHealth Group Inc.", "symbol": "UNH", "type": "stock", "sector": "Healthcare"},
    "eq-XOM": {"yf": "XOM", "name": "Exxon Mobil Corp.", "symbol": "XOM", "type": "stock", "sector": "Energy"},
    "eq-PG": {"yf": "PG", "name": "Procter & Gamble Co.", "symbol": "PG", "type": "stock", "sector": "Consumer Defensive"},
    "eq-MA": {"yf": "MA", "name": "Mastercard Inc.", "symbol": "MA", "type": "stock", "sector": "Financial Services"},
    "eq-HD": {"yf": "HD", "name": "Home Depot Inc.", "symbol": "HD", "type": "stock", "sector": "Consumer Cyclical"},
    "eq-BAC": {"yf": "BAC", "name": "Bank of America Corp.", "symbol": "BAC", "type": "stock", "sector": "Financial Services"},
    "eq-NFLX": {"yf": "NFLX", "name": "Netflix Inc.", "symbol": "NFLX", "type": "stock", "sector": "Technology"},
    "eq-AMD": {"yf": "AMD", "name": "Advanced Micro Devices Inc.", "symbol": "AMD", "type": "stock", "sector": "Technology"},
    "eq-CRM": {"yf": "CRM", "name": "Salesforce Inc.", "symbol": "CRM", "type": "stock", "sector": "Technology"},
    # Major ETFs
    "etf-SPY": {"yf": "SPY", "name": "Invesco S&P 500 ETF", "symbol": "SPY", "type": "etf", "sector": "Broad Market"},
    "etf-QQQ": {"yf": "QQQ", "name": "Invesco QQQ Trust", "symbol": "QQQ", "type": "etf", "sector": "Tech-Heavy"},
    "etf-IWM": {"yf": "IWM", "name": "iShares Russell 2000 ETF", "symbol": "IWM", "type": "etf", "sector": "Small Cap"},
    "etf-DIA": {"yf": "DIA", "name": "SPDR Dow Jones Industrial ETF", "symbol": "DIA", "type": "etf", "sector": "Large Cap"},
    "etf-VTI": {"yf": "VTI", "name": "Vanguard Total Stock Market ETF", "symbol": "VTI", "type": "etf", "sector": "Broad Market"},
    "etf-EEM": {"yf": "EEM", "name": "iShares MSCI Emerging Markets ETF", "symbol": "EEM", "type": "etf", "sector": "International"},
    "etf-GLD": {"yf": "GLD", "name": "SPDR Gold Shares", "symbol": "GLD", "type": "etf", "sector": "Commodities"},
    "etf-TLT": {"yf": "TLT", "name": "iShares 20+ Year Treasury ETF", "symbol": "TLT", "type": "etf", "sector": "Bonds"},
    "etf-XLF": {"yf": "XLF", "name": "Financial Select Sector SPDR", "symbol": "XLF", "type": "etf", "sector": "Financial"},
    "etf-XLE": {"yf": "XLE", "name": "Energy Select Sector SPDR", "symbol": "XLE", "type": "etf", "sector": "Energy"},
}


def _format_volume(vol: float) -> str:
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.1f}B"
    elif vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    else:
        return f"${vol / 1_000:.0f}K"


def _format_market_cap(market_cap: Optional[float]) -> str:
    if market_cap is None:
        return "N/A"
    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.1f}T"
    elif market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.1f}B"
    elif market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.1f}M"
    else:
        return f"${market_cap / 1_000:.0f}K"


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


class EquityDataProvider:
    """
    Real equity and ETF data provider using yfinance.

    Fetches real stock/ETF prices, caches them, computes technical indicators,
    and provides fundamental data for screening.
    """

    def __init__(self, refresh_interval: float = 30.0):
        self.refresh_interval = refresh_interval
        self._prices: dict[str, CachedPrice] = {}
        self._historical: dict[str, pd.DataFrame] = {}  # market_id -> OHLCV DataFrame
        self._indicators: dict[str, dict] = {}  # market_id -> latest indicator values
        self._fundamentals: dict[str, dict] = {}  # ticker -> fundamental data
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_fetch: float = 0

    # ─── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the background price refresh loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._safe_refresh_loop())
            logger.info("Equity data provider started")

    async def _safe_refresh_loop(self):
        """Wrapper that catches and logs any crash in the refresh loop."""
        try:
            await self._refresh_loop()
        except Exception as e:
            logger.error(f"EQUITY REFRESH LOOP CRASHED: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def is_running(self) -> bool:
        return self._running and len(self._prices) > 0

    async def _refresh_loop(self):
        """Periodically fetch latest prices from Yahoo Finance."""
        try:
            # Initial price fetch (most important — do first)
            await self._fetch_all_prices()
            logger.info(f"Equity initial prices loaded: {len(self._prices)} tickers")
        except Exception as e:
            logger.error(f"Equity initial price fetch failed: {e}")

        try:
            await self._fetch_all_historical()
        except Exception as e:
            logger.error(f"Equity historical fetch failed: {e}")

        try:
            await self._fetch_all_fundamentals()
        except Exception as e:
            logger.error(f"Equity fundamentals fetch failed: {e}")

        while self._running:
            await asyncio.sleep(self.refresh_interval)
            try:
                await self._fetch_all_prices()
            except Exception as e:
                logger.error(f"Price refresh error: {e}")

    async def _fetch_all_prices(self):
        """Fetch current prices for all tracked symbols using individual ticker calls."""
        loop = asyncio.get_event_loop()
        now = time.time()

        for market_id, meta in EQUITY_SYMBOLS.items():
            try:
                result = await loop.run_in_executor(
                    None, self._fetch_single_price, meta["yf"]
                )
                if result:
                    price, high, low, volume, change_pct = result

                    # Simulate bid/ask spread (tight for large caps)
                    spread = price * 0.0002
                    self._prices[market_id] = CachedPrice(
                        price=price,
                        bid=round(price - spread / 2, 2),
                        ask=round(price + spread / 2, 2),
                        change_24h=round(change_pct, 2),
                        volume_24h=volume * price,
                        high_24h=high,
                        low_24h=low,
                        updated_at=now,
                    )
            except Exception as e:
                logger.debug(f"Error fetching {market_id}: {e}")

        self._last_fetch = now
        logger.info(f"Updated {len(self._prices)} equity prices")

    def _fetch_single_price(self, yf_ticker: str):
        """Synchronous single-ticker price fetch (called in executor)."""
        try:
            ticker = yf.Ticker(yf_ticker)
            hist = ticker.history(period="5d")
            if hist is None or hist.empty:
                return None

            price = float(hist["Close"].iloc[-1])
            if price <= 0:
                return None

            high = float(hist["High"].iloc[-1])
            low = float(hist["Low"].iloc[-1])
            volume = float(hist["Volume"].iloc[-1])

            # Get previous close for change calc
            if len(hist) >= 2:
                prev_close = float(hist["Close"].iloc[-2])
            else:
                prev_close = float(hist["Open"].iloc[-1])

            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            return (price, high, low, volume, change_pct)
        except Exception as e:
            logger.debug(f"Error fetching {yf_ticker}: {e}")
            return None

    async def _fetch_all_historical(self):
        """Fetch 90 days of daily OHLCV data for strategy calculations."""
        loop = asyncio.get_event_loop()
        for market_id, meta in EQUITY_SYMBOLS.items():
            try:
                df = await loop.run_in_executor(
                    None,
                    lambda t=meta["yf"]: yf.Ticker(t).history(period="90d")
                )
                if df is not None and not df.empty:
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

    async def _fetch_all_fundamentals(self):
        """Fetch fundamental data for stocks."""
        for market_id, meta in EQUITY_SYMBOLS.items():
            if meta["type"] != "stock":
                continue
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._fetch_fundamentals_sync, meta["yf"])
            except Exception as e:
                logger.debug(f"Fundamental fetch error for {meta['yf']}: {e}")

    def _fetch_fundamentals_sync(self, ticker: str):
        """Synchronous fundamental data fetch (called in executor)."""
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            fundamentals = {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "employees": info.get("fullTimeEmployees"),
                "website": info.get("website"),
                "updated_at": time.time(),
            }

            self._fundamentals[ticker] = fundamentals
            logger.debug(f"Loaded fundamentals for {ticker}")
        except Exception as e:
            logger.debug(f"Error fetching fundamentals for {ticker}: {e}")

    # ─── Public API ──────────────────────────────────────────

    def get_markets(self, market_type: str = "", search: str = "", limit: int = 50) -> list[dict]:
        """Get all markets with real price data."""
        results = []
        for market_id, meta in EQUITY_SYMBOLS.items():
            if market_type and meta["type"] != market_type:
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
                "type": meta["type"],
                "sector": meta["sector"],
                "description": f"{meta['name']} — real market data",
                "price": round(cached.price, 2),
                "change": round(cached.change_24h / 100, 4),  # As fraction
                "volume": _format_volume(cached.volume_24h),
                "category": "equities",
                "active": True,
                "dataSource": "live",
                "high24h": round(cached.high_24h, 2),
                "low24h": round(cached.low_24h, 2),
            }

            # Add fundamental data for stocks
            if meta["type"] == "stock":
                fund = self._fundamentals.get(meta["yf"], {})
                d["marketCap"] = _format_market_cap(fund.get("market_cap"))
                d["peRatio"] = round(fund.get("pe_ratio"), 2) if fund.get("pe_ratio") else "N/A"
                d["eps"] = round(fund.get("eps"), 2) if fund.get("eps") else "N/A"
                d["dividendYield"] = round(fund.get("dividend_yield", 0) * 100, 2) if fund.get("dividend_yield") else 0

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
            bid_size = round(100 + i * 50, 0)
            ask_size = round(100 + i * 50, 0)
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

    def get_fundamentals(self, ticker: str) -> dict:
        """Get fundamental data for a ticker."""
        return self._fundamentals.get(ticker, {})

    def get_screener(self, min_market_cap: Optional[float] = None, max_pe: Optional[float] = None,
                     min_dividend_yield: float = 0.0, sector: Optional[str] = None) -> list[dict]:
        """
        Filter stocks by fundamental criteria.

        Args:
            min_market_cap: Minimum market cap in USD
            max_pe: Maximum P/E ratio
            min_dividend_yield: Minimum dividend yield (0-1 scale)
            sector: Filter by sector name

        Returns:
            List of matching stocks with fundamental data
        """
        results = []

        for market_id, meta in EQUITY_SYMBOLS.items():
            if meta["type"] != "stock":
                continue

            if sector and meta["sector"] != sector:
                continue

            fund = self._fundamentals.get(meta["yf"], {})
            market_cap = fund.get("market_cap")
            pe_ratio = fund.get("pe_ratio")
            div_yield = fund.get("dividend_yield", 0) or 0

            if min_market_cap and (market_cap is None or market_cap < min_market_cap):
                continue

            if max_pe and (pe_ratio is None or pe_ratio > max_pe):
                continue

            if div_yield < min_dividend_yield:
                continue

            cached = self._prices.get(market_id)
            if cached:
                results.append({
                    "id": market_id,
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "price": round(cached.price, 2),
                    "market_cap": _format_market_cap(market_cap),
                    "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
                    "dividend_yield": round(div_yield * 100, 2),
                    "sector": meta["sector"],
                })

        return results

    async def refresh_historical(self):
        """Force refresh historical data and recompute indicators."""
        await self._fetch_all_historical()
