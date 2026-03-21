"""
Base connector interface.

Every exchange/platform connector (Polymarket, Binance, Uniswap, Hyperliquid)
must inherit from this class and implement these methods. This gives us a
uniform API across all platforms, so the trading engine doesn't care which
platform it's talking to.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ─── Shared Data Models ─────────────────────────────────────────────

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"       # Execute immediately at best price
    LIMIT = "limit"         # Execute at specified price or better
    GTC = "gtc"             # Good-Till-Cancelled (limit that stays open)
    FOK = "fok"             # Fill-Or-Kill (fill entirely or cancel)


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Market:
    """Represents a tradeable market on any platform."""
    id: str                          # Platform-specific market ID
    name: str                        # Human-readable name
    platform: str                    # e.g., "polymarket", "binance"
    description: str = ""
    active: bool = True
    extra: dict = field(default_factory=dict)  # Platform-specific data


@dataclass
class OrderBook:
    """Order book snapshot."""
    market_id: str
    bids: list[dict]                 # [{"price": 0.65, "size": 100}, ...]
    asks: list[dict]                 # [{"price": 0.67, "size": 50}, ...]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0]["price"] if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0]["price"] if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


@dataclass
class Order:
    """Represents an order placed on any platform."""
    id: str
    market_id: str
    side: OrderSide
    order_type: OrderType
    price: float
    size: float
    status: OrderStatus = OrderStatus.PENDING
    filled_size: float = 0.0
    platform: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    extra: dict = field(default_factory=dict)


@dataclass
class Position:
    """Represents a current holding/position."""
    market_id: str
    side: OrderSide
    size: float                      # Number of shares/contracts
    entry_price: float               # Average entry price
    current_price: float = 0.0
    platform: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss."""
        if self.side == OrderSide.BUY:
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size

    @property
    def pnl_percent(self) -> float:
        """P&L as a percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.unrealized_pnl / (self.entry_price * self.size)) * 100


# ─── Abstract Base Connector ────────────────────────────────────────

class BaseConnector(ABC):
    """
    Abstract base class for all exchange/platform connectors.

    Every connector must implement these methods so the trading engine
    can interact with any platform through a uniform interface.
    """

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # --- Connection ---

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the platform.
        Returns True if successful.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connections and resources."""
        pass

    # --- Market Data (read-only, no auth needed) ---

    @abstractmethod
    async def get_markets(self, **filters) -> list[Market]:
        """
        Fetch available markets.
        Filters are platform-specific (e.g., active=True, keyword="election").
        """
        pass

    @abstractmethod
    async def get_market(self, market_id: str) -> Market:
        """Fetch a single market by ID."""
        pass

    @abstractmethod
    async def get_orderbook(self, market_id: str) -> OrderBook:
        """Fetch the current order book for a market."""
        pass

    @abstractmethod
    async def get_price(self, market_id: str, side: OrderSide) -> float:
        """Get the current best price for a side (buy/sell)."""
        pass

    # --- Trading (requires auth) ---

    @abstractmethod
    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        order_type: OrderType,
        size: float,
        price: Optional[float] = None,
    ) -> Order:
        """
        Place an order on the platform.

        Args:
            market_id: Which market to trade
            side: BUY or SELL
            order_type: MARKET, LIMIT, GTC, FOK
            size: How many shares/contracts
            price: Required for limit orders, ignored for market orders

        Returns:
            Order object with status and platform-assigned ID
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order. Returns True if successful."""
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get the current status of an order."""
        pass

    @abstractmethod
    async def get_open_orders(self, market_id: Optional[str] = None) -> list[Order]:
        """Get all open orders, optionally filtered by market."""
        pass

    # --- Portfolio ---

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all current positions/holdings."""
        pass

    @abstractmethod
    async def get_balance(self) -> dict:
        """
        Get account balance.
        Returns dict like {"usdc": 1000.0, "total_value": 1500.0}
        """
        pass
