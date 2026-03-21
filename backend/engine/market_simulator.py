"""
Market Data Simulator — generates realistic price feeds without real API.

Simulates multiple platforms:
- Polymarket: Prediction markets (prices 0.01-0.99)
- Binance: Crypto spot pairs (real-ish prices)
- Hyperliquid: Perpetual contracts with funding rates

All prices use random walk with mean reversion.
"""

import asyncio
import random
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class SimulatedMarket:
    """A single simulated market on any platform."""
    id: str
    name: str
    platform: str = "polymarket"    # polymarket | binance | hyperliquid
    market_type: str = "prediction"  # prediction | spot | perp
    description: str = ""
    symbol: str = ""                 # Trading pair symbol (e.g., BTC/USDT)
    true_price: float = 0.50
    volatility: float = 0.002
    drift: float = 0.0
    volume_24h: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    end_date: str = ""
    category: str = "general"

    # Perp-specific fields
    funding_rate: float = 0.0
    open_interest: float = 0.0
    leverage_max: int = 1

    # Price bounds (prediction = 0.01-0.99, spot/perp = no ceiling)
    price_min: float = 0.02
    price_max: float = 0.98

    # Track price history for charts
    price_history: list = field(default_factory=list)
    _last_update: float = field(default_factory=time.time)

    def tick(self) -> float:
        """Advance the price by one tick (random walk with mean reversion)."""
        if self.market_type == "prediction":
            # Mean reversion toward 0.50 (mild)
            reversion = (0.50 - self.true_price) * 0.0005
        else:
            # Mean reversion toward initial price (very mild for spot/perp)
            reversion = 0

        noise = random.gauss(0, self.volatility)
        self.true_price += self.drift + reversion + noise
        self.true_price = max(self.price_min, min(self.price_max, self.true_price))

        # Record history (keep last 500 ticks)
        now = time.time()
        self.price_history.append({
            "time": now,
            "price": round(self.true_price, 4 if self.market_type == "prediction" else 2),
        })
        if len(self.price_history) > 500:
            self.price_history = self.price_history[-500:]

        # Simulate volume
        self.volume_24h += random.uniform(50, 500)

        # Update funding rate for perps (slight random walk)
        if self.market_type == "perp":
            self.funding_rate += random.gauss(0, 0.0001)
            self.funding_rate = max(-0.01, min(0.01, self.funding_rate))
            self.open_interest += random.uniform(-5000, 10000)
            self.open_interest = max(100_000, self.open_interest)

        self._last_update = now
        return self.true_price

    def get_bid_price(self) -> float:
        """Best bid (slightly below true price)."""
        if self.market_type == "prediction":
            spread = random.uniform(0.005, 0.015)
        else:
            spread = self.true_price * random.uniform(0.0003, 0.001)
        return round(max(self.price_min, self.true_price - spread / 2), 4 if self.market_type == "prediction" else 2)

    def get_ask_price(self) -> float:
        """Best ask (slightly above true price)."""
        if self.market_type == "prediction":
            spread = random.uniform(0.005, 0.015)
        else:
            spread = self.true_price * random.uniform(0.0003, 0.001)
        return round(min(self.price_max, self.true_price + spread / 2), 4 if self.market_type == "prediction" else 2)

    def get_orderbook(self) -> dict:
        """Generate a realistic order book around current price."""
        bids = []
        asks = []
        bid_base = self.get_bid_price()
        ask_base = self.get_ask_price()

        if self.market_type == "prediction":
            step = 0.01
            levels = 8
        else:
            step = self.true_price * 0.001  # 0.1% per level
            levels = 8

        for i in range(levels):
            bid_price = round(bid_base - i * step, 4 if self.market_type == "prediction" else 2)
            ask_price = round(ask_base + i * step, 4 if self.market_type == "prediction" else 2)

            if bid_price > self.price_min:
                bid_size = round(random.uniform(200, 2000) * (1 + i * 0.5))
                if self.market_type != "prediction":
                    bid_size = round(random.uniform(0.1, 5.0) * (1 + i * 0.3), 4)
                bids.append({"price": bid_price, "size": bid_size})

            if ask_price < self.price_max:
                ask_size = round(random.uniform(200, 2000) * (1 + i * 0.5))
                if self.market_type != "prediction":
                    ask_size = round(random.uniform(0.1, 5.0) * (1 + i * 0.3), 4)
                asks.append({"price": ask_price, "size": ask_size})

        return {"bids": bids, "asks": asks}

    def get_price_change(self) -> float:
        """Price change in last ~100 ticks as fraction."""
        if len(self.price_history) < 2:
            return 0.0
        old = self.price_history[max(0, len(self.price_history) - 100)]["price"]
        if old == 0:
            return 0.0
        return round((self.true_price - old) / old, 4)


# ─── Seed markets per platform ─────────────────────────────────

POLYMARKET_MARKETS = [
    SimulatedMarket(
        id="poly-btc-150k", name="Will Bitcoin reach $150k by July 2026?",
        platform="polymarket", market_type="prediction", symbol="BTC-150K",
        description="Resolves YES if BTC/USD trades at or above $150,000 on any major exchange before July 31, 2026.",
        true_price=0.42, volatility=0.003, drift=0.0002, volume_24h=1_200_000,
        end_date="2026-07-31", category="crypto",
    ),
    SimulatedMarket(
        id="poly-fed-rate-cut", name="Fed rate cut in June 2026?",
        platform="polymarket", market_type="prediction", symbol="FED-RATE",
        description="Resolves YES if the Federal Reserve cuts the federal funds rate at or before the June 2026 FOMC meeting.",
        true_price=0.68, volatility=0.002, drift=0.0001, volume_24h=890_000,
        end_date="2026-06-15", category="economics",
    ),
    SimulatedMarket(
        id="poly-gpt5-launch", name="Will GPT-5 launch before August 2026?",
        platform="polymarket", market_type="prediction", symbol="GPT5",
        description="Resolves YES if OpenAI publicly releases a model officially named GPT-5 before August 1, 2026.",
        true_price=0.55, volatility=0.004, drift=-0.0001, volume_24h=2_100_000,
        end_date="2026-08-01", category="tech",
    ),
    SimulatedMarket(
        id="poly-eth-etf", name="Will Ethereum ETF see $1B inflows in Q2?",
        platform="polymarket", market_type="prediction", symbol="ETH-ETF",
        description="Resolves YES if cumulative net inflows into all US spot Ethereum ETFs exceed $1 billion in Q2 2026.",
        true_price=0.38, volatility=0.003, drift=0.00015, volume_24h=450_000,
        end_date="2026-06-30", category="crypto",
    ),
    SimulatedMarket(
        id="poly-trump-2028", name="Trump wins 2028 Republican primary?",
        platform="polymarket", market_type="prediction", symbol="TRUMP-2028",
        description="Resolves YES if Donald Trump wins the 2028 Republican presidential primary nomination.",
        true_price=0.62, volatility=0.002, drift=0.0, volume_24h=3_800_000,
        end_date="2028-08-01", category="politics",
    ),
    SimulatedMarket(
        id="poly-ai-regulation", name="US passes AI regulation bill in 2026?",
        platform="polymarket", market_type="prediction", symbol="AI-REG",
        description="Resolves YES if the US Congress passes a comprehensive AI regulation bill signed into law in 2026.",
        true_price=0.25, volatility=0.002, drift=0.0001, volume_24h=320_000,
        end_date="2026-12-31", category="politics",
    ),
]

BINANCE_MARKETS = [
    SimulatedMarket(
        id="bin-btc-usdt", name="BTC/USDT", platform="binance", market_type="spot",
        symbol="BTC/USDT", description="Bitcoin / Tether spot",
        true_price=87450.0, volatility=85.0, drift=5.0, volume_24h=28_500_000_000,
        category="crypto", price_min=1000.0, price_max=500000.0,
    ),
    SimulatedMarket(
        id="bin-eth-usdt", name="ETH/USDT", platform="binance", market_type="spot",
        symbol="ETH/USDT", description="Ethereum / Tether spot",
        true_price=3280.0, volatility=12.0, drift=1.5, volume_24h=12_800_000_000,
        category="crypto", price_min=100.0, price_max=50000.0,
    ),
    SimulatedMarket(
        id="bin-sol-usdt", name="SOL/USDT", platform="binance", market_type="spot",
        symbol="SOL/USDT", description="Solana / Tether spot",
        true_price=142.0, volatility=1.2, drift=0.1, volume_24h=3_200_000_000,
        category="crypto", price_min=5.0, price_max=1000.0,
    ),
    SimulatedMarket(
        id="bin-bnb-usdt", name="BNB/USDT", platform="binance", market_type="spot",
        symbol="BNB/USDT", description="BNB / Tether spot",
        true_price=605.0, volatility=3.5, drift=0.3, volume_24h=1_800_000_000,
        category="crypto", price_min=50.0, price_max=5000.0,
    ),
    SimulatedMarket(
        id="bin-xrp-usdt", name="XRP/USDT", platform="binance", market_type="spot",
        symbol="XRP/USDT", description="XRP / Tether spot",
        true_price=2.35, volatility=0.02, drift=0.001, volume_24h=2_500_000_000,
        category="crypto", price_min=0.10, price_max=100.0,
    ),
    SimulatedMarket(
        id="bin-doge-usdt", name="DOGE/USDT", platform="binance", market_type="spot",
        symbol="DOGE/USDT", description="Dogecoin / Tether spot",
        true_price=0.168, volatility=0.002, drift=0.0001, volume_24h=1_100_000_000,
        category="crypto", price_min=0.001, price_max=10.0,
    ),
]

HYPERLIQUID_MARKETS = [
    SimulatedMarket(
        id="hl-btc-perp", name="BTC-PERP", platform="hyperliquid", market_type="perp",
        symbol="BTC-PERP", description="Bitcoin perpetual contract",
        true_price=87480.0, volatility=90.0, drift=3.0, volume_24h=4_200_000_000,
        category="crypto", price_min=1000.0, price_max=500000.0,
        funding_rate=0.0001, open_interest=850_000_000, leverage_max=50,
    ),
    SimulatedMarket(
        id="hl-eth-perp", name="ETH-PERP", platform="hyperliquid", market_type="perp",
        symbol="ETH-PERP", description="Ethereum perpetual contract",
        true_price=3285.0, volatility=14.0, drift=1.0, volume_24h=2_800_000_000,
        category="crypto", price_min=100.0, price_max=50000.0,
        funding_rate=0.00008, open_interest=420_000_000, leverage_max=50,
    ),
    SimulatedMarket(
        id="hl-sol-perp", name="SOL-PERP", platform="hyperliquid", market_type="perp",
        symbol="SOL-PERP", description="Solana perpetual contract",
        true_price=142.5, volatility=1.5, drift=0.05, volume_24h=1_500_000_000,
        category="crypto", price_min=5.0, price_max=1000.0,
        funding_rate=0.00012, open_interest=180_000_000, leverage_max=20,
    ),
    SimulatedMarket(
        id="hl-arb-perp", name="ARB-PERP", platform="hyperliquid", market_type="perp",
        symbol="ARB-PERP", description="Arbitrum perpetual contract",
        true_price=1.12, volatility=0.01, drift=0.0, volume_24h=320_000_000,
        category="crypto", price_min=0.05, price_max=100.0,
        funding_rate=-0.00005, open_interest=45_000_000, leverage_max=20,
    ),
    SimulatedMarket(
        id="hl-wif-perp", name="WIF-PERP", platform="hyperliquid", market_type="perp",
        symbol="WIF-PERP", description="dogwifhat perpetual contract",
        true_price=0.82, volatility=0.012, drift=0.0, volume_24h=180_000_000,
        category="meme", price_min=0.01, price_max=50.0,
        funding_rate=0.0003, open_interest=25_000_000, leverage_max=10,
    ),
]


def _format_volume(vol: float) -> str:
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.1f}B"
    elif vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    else:
        return f"${vol / 1_000:.0f}K"


def _market_to_dict(m: SimulatedMarket) -> dict:
    """Convert a SimulatedMarket to API-friendly dict."""
    decimals = 4 if m.market_type == "prediction" else 2
    d = {
        "id": m.id,
        "name": m.name,
        "symbol": m.symbol,
        "platform": m.platform,
        "marketType": m.market_type,
        "description": m.description,
        "price": round(m.true_price, decimals),
        "change": m.get_price_change(),
        "volume": _format_volume(m.volume_24h),
        "category": m.category,
        "active": True,
    }
    if m.market_type == "prediction":
        d["endDate"] = m.end_date
    if m.market_type == "perp":
        d["fundingRate"] = round(m.funding_rate, 6)
        d["openInterest"] = _format_volume(m.open_interest)
        d["leverageMax"] = m.leverage_max
    return d


class MarketSimulator:
    """
    Manages all simulated markets across platforms and ticks them forward.

    Usage:
        sim = MarketSimulator()
        sim.start()
        markets = sim.get_markets(platform="binance")
    """

    PLATFORMS = {
        "polymarket": {"label": "Polymarket", "type": "prediction", "icon": "target"},
        "binance":    {"label": "Binance",    "type": "spot",       "icon": "coins"},
        "hyperliquid":{"label": "Hyperliquid","type": "perp",       "icon": "zap"},
    }

    def __init__(self):
        self.markets: dict[str, SimulatedMarket] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Load all seed markets
        for m in POLYMARKET_MARKETS + BINANCE_MARKETS + HYPERLIQUID_MARKETS:
            self.markets[m.id] = m

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._tick_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _tick_loop(self):
        while self._running:
            for market in self.markets.values():
                market.tick()
            await asyncio.sleep(1)

    def get_platforms(self) -> list[dict]:
        """Get all available platforms with market counts."""
        result = []
        for pid, meta in self.PLATFORMS.items():
            count = sum(1 for m in self.markets.values() if m.platform == pid)
            result.append({
                "id": pid,
                "label": meta["label"],
                "type": meta["type"],
                "icon": meta["icon"],
                "marketCount": count,
            })
        return result

    def get_markets(self, platform: str = "", search: str = "", limit: int = 50) -> list[dict]:
        """Get markets, optionally filtered by platform and/or search term."""
        results = []
        for m in self.markets.values():
            if platform and m.platform != platform:
                continue
            if search and search.lower() not in m.name.lower() and search.lower() not in m.symbol.lower():
                continue
            results.append(_market_to_dict(m))
        return results[:limit]

    def get_market(self, market_id: str) -> Optional[dict]:
        m = self.markets.get(market_id)
        if not m:
            return None
        return _market_to_dict(m)

    def get_price(self, market_id: str, side: str = "buy") -> float:
        m = self.markets.get(market_id)
        if not m:
            return 0.0
        return m.get_bid_price() if side == "sell" else m.get_ask_price()

    def get_orderbook(self, market_id: str) -> dict:
        m = self.markets.get(market_id)
        if not m:
            return {"bids": [], "asks": []}
        return m.get_orderbook()

    def get_price_history(self, market_id: str) -> list[dict]:
        m = self.markets.get(market_id)
        if not m:
            return []
        return m.price_history
