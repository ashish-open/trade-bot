"""
Paper Trading Engine — simulates order execution and tracks positions.

Manages:
- Placing buy/sell orders (limit and market)
- Matching orders against simulated prices
- Position tracking with real-time P&L
- Trade history and portfolio stats
- Starting balance and cash management
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backend.engine.market_simulator import MarketSimulator


@dataclass
class PaperOrder:
    id: str
    market_id: str
    market_name: str
    side: str           # "buy" or "sell"
    order_type: str     # "market" or "limit"
    price: float        # Limit price (0 for market orders)
    size: float         # Number of shares
    status: str = "open"  # open, filled, cancelled
    filled_price: float = 0.0
    filled_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PaperPosition:
    market_id: str
    market_name: str
    platform: str       # polymarket | binance | hyperliquid
    side: str           # "YES"/"NO" (prediction) or "LONG"/"SHORT" (spot/perp)
    size: float         # Shares held
    entry_price: float  # Average entry price
    cost_basis: float   # Total money spent


@dataclass
class PaperTrade:
    """A completed trade (filled order)."""
    id: str
    market_id: str
    market_name: str
    side: str
    price: float
    size: float
    pnl: Optional[float]  # Realized P&L (for sells)
    timestamp: str


class PaperTradingEngine:
    """
    Paper trading engine that simulates real trading against the market simulator.

    Usage:
        engine = PaperTradingEngine(simulator, starting_balance=10000)
        order = engine.place_order("sim-btc-150k", "buy", "limit", size=100, price=0.42)
        engine.check_fills()  # Call periodically to match limit orders
        portfolio = engine.get_portfolio()
    """

    def __init__(self, simulator: MarketSimulator, starting_balance: float = 10000.0):
        self.simulator = simulator
        self.starting_balance = starting_balance
        self.cash = starting_balance

        self.orders: dict[str, PaperOrder] = {}
        self.positions: dict[str, PaperPosition] = {}  # Keyed by market_id
        self.trades: list[PaperTrade] = []

    # ── Order Placement ──────────────────────────────────────────

    def place_order(
        self,
        market_id: str,
        side: str,
        order_type: str = "market",
        size: float = 0,
        price: float = 0,
    ) -> dict:
        """
        Place a paper order.

        Args:
            market_id: Which simulated market
            side: "buy" or "sell"
            order_type: "market" or "limit"
            size: Number of shares
            price: Required for limit orders

        Returns:
            Order dict with id and status
        """
        market = self.simulator.get_market(market_id)
        if not market:
            return {"error": f"Market {market_id} not found"}

        if size <= 0:
            return {"error": "Size must be positive"}

        if side == "buy":
            # Check if we have enough cash
            fill_price = price if order_type == "limit" else self.simulator.get_price(market_id, "buy")
            cost = fill_price * size
            if cost > self.cash:
                return {"error": f"Insufficient funds. Need ${cost:.2f}, have ${self.cash:.2f}"}
        elif side == "sell":
            # Check if we have enough shares
            pos = self.positions.get(market_id)
            if not pos or pos.size < size:
                available = pos.size if pos else 0
                return {"error": f"Insufficient shares. Have {available}, trying to sell {size}"}

        order_id = f"paper-{uuid.uuid4().hex[:8]}"
        order = PaperOrder(
            id=order_id,
            market_id=market_id,
            market_name=market["name"],
            side=side,
            order_type=order_type,
            price=price,
            size=size,
        )

        if order_type == "market":
            # Fill immediately
            fill_price = self.simulator.get_price(market_id, side)
            self._fill_order(order, fill_price)
        else:
            # Limit order — add to open orders, will check for fills later
            self.orders[order_id] = order

        return {
            "id": order.id,
            "status": order.status,
            "side": order.side,
            "price": order.filled_price or order.price,
            "size": order.size,
            "market": order.market_name,
        }

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an open limit order."""
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        if order.status != "open":
            return {"error": f"Order is already {order.status}"}

        order.status = "cancelled"
        return {"success": True, "id": order_id}

    # ── Order Matching ───────────────────────────────────────────

    def check_fills(self):
        """
        Check all open limit orders for fills.
        Call this periodically (e.g., every tick from the API).
        """
        for order in list(self.orders.values()):
            if order.status != "open":
                continue

            current_price = self.simulator.get_price(order.market_id, order.side)

            if order.side == "buy" and current_price <= order.price:
                # Buy limit hit — fill at our limit price
                self._fill_order(order, order.price)
            elif order.side == "sell" and current_price >= order.price:
                # Sell limit hit — fill at our limit price
                self._fill_order(order, order.price)

    def _fill_order(self, order: PaperOrder, fill_price: float):
        """Execute an order fill — update positions and cash."""
        order.status = "filled"
        order.filled_price = fill_price
        order.filled_at = datetime.utcnow().isoformat()

        pnl = None

        if order.side == "buy":
            cost = fill_price * order.size
            self.cash -= cost

            # Update or create position
            pos = self.positions.get(order.market_id)
            if pos:
                # Average in
                total_cost = pos.cost_basis + cost
                total_size = pos.size + order.size
                pos.entry_price = total_cost / total_size
                pos.size = total_size
                pos.cost_basis = total_cost
            else:
                # Determine platform and position side label
                sim_market = self.simulator.markets.get(order.market_id)
                platform = sim_market.platform if sim_market else "paper"
                side_label = "LONG" if sim_market and sim_market.market_type != "prediction" else "YES"
                self.positions[order.market_id] = PaperPosition(
                    market_id=order.market_id,
                    market_name=order.market_name,
                    platform=platform,
                    side=side_label,
                    size=order.size,
                    entry_price=fill_price,
                    cost_basis=cost,
                )

        elif order.side == "sell":
            revenue = fill_price * order.size
            self.cash += revenue

            pos = self.positions.get(order.market_id)
            if pos:
                pnl = (fill_price - pos.entry_price) * order.size
                pos.size -= order.size
                pos.cost_basis = pos.entry_price * pos.size

                # Remove position if fully closed
                if pos.size <= 0.001:
                    del self.positions[order.market_id]

        # Record the trade
        self.trades.append(PaperTrade(
            id=order.id,
            market_id=order.market_id,
            market_name=order.market_name,
            side=order.side,
            price=fill_price,
            size=order.size,
            pnl=round(pnl, 2) if pnl is not None else None,
            timestamp=order.filled_at or datetime.utcnow().isoformat(),
        ))

    # ── Portfolio & Stats ────────────────────────────────────────

    def get_portfolio(self) -> dict:
        """Get full portfolio summary."""
        positions_value = 0
        total_unrealized_pnl = 0

        position_list = []
        for pos in self.positions.values():
            current_price = self.simulator.get_price(pos.market_id, "sell")
            market_value = current_price * pos.size
            unrealized = (current_price - pos.entry_price) * pos.size
            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0

            positions_value += market_value
            total_unrealized_pnl += unrealized

            platform_labels = {"polymarket": "Polymarket", "binance": "Binance", "hyperliquid": "Hyperliquid"}
            position_list.append({
                "id": pos.market_id,
                "market": pos.market_name,
                "platform": platform_labels.get(pos.platform, pos.platform.title()),
                "side": pos.side,
                "size": pos.size,
                "entryPrice": round(pos.entry_price, 4),
                "currentPrice": round(current_price, 4),
                "pnl": round(unrealized, 2),
                "pnlPercent": round(pnl_pct, 2),
            })

        total_value = self.cash + positions_value
        total_pnl = total_value - self.starting_balance

        # Win rate from completed trades
        sell_trades = [t for t in self.trades if t.pnl is not None]
        wins = sum(1 for t in sell_trades if t.pnl >= 0)
        win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0

        return {
            "totalValue": round(total_value, 2),
            "cash": round(self.cash, 2),
            "positionsValue": round(positions_value, 2),
            "totalPnl": round(total_pnl, 2),
            "totalPnlPercent": round((total_pnl / self.starting_balance) * 100, 2),
            "dayPnl": round(total_unrealized_pnl, 2),
            "dayPnlPercent": round((total_unrealized_pnl / max(total_value, 1)) * 100, 2),
            "winRate": round(win_rate, 1),
            "totalTrades": len(self.trades),
            "openPositions": len(self.positions),
            "activeStrategies": 0,
            "positions": position_list,
        }

    def get_positions(self) -> list[dict]:
        """Get current positions."""
        return self.get_portfolio()["positions"]

    def get_open_orders(self) -> list[dict]:
        """Get all open orders."""
        return [
            {
                "id": o.id,
                "market": o.market_name,
                "marketId": o.market_id,
                "side": o.side,
                "type": o.order_type,
                "price": o.price,
                "size": o.size,
                "status": o.status,
                "createdAt": o.created_at,
            }
            for o in self.orders.values()
            if o.status == "open"
        ]

    def get_trade_history(self, limit: int = 50) -> list[dict]:
        """Get recent trades, newest first."""
        trades = sorted(self.trades, key=lambda t: t.timestamp, reverse=True)
        return [
            {
                "id": t.id,
                "time": t.timestamp[11:19] if "T" in t.timestamp else t.timestamp,
                "market": t.market_name,
                "side": t.side.upper(),
                "price": t.price,
                "size": t.size,
                "status": "filled",
                "pnl": t.pnl,
            }
            for t in trades[:limit]
        ]
