"""
Polymarket Connector — Full integration with Polymarket's CLOB, Gamma, and Data APIs.

This connector handles:
1. Market discovery (Gamma API — no auth needed)
2. Price/orderbook data (CLOB API — no auth needed)
3. Order placement & management (CLOB API — auth required)
4. Position tracking (Data API — no auth needed)

Authentication uses your Ethereum private key (from MetaMask) to derive
API credentials via EIP-712 signature. Your private key never leaves your machine.

Platform: Polymarket (https://polymarket.com)
Chain: Polygon (chain_id=137)
"""

import asyncio
import httpx
from typing import Optional
from loguru import logger

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType as PMOrderType
from py_clob_client.order_builder.constants import BUY, SELL

from backend.connectors.base import (
    BaseConnector,
    Market,
    OrderBook,
    Order,
    Position,
    OrderSide,
    OrderType,
    OrderStatus,
)
from backend.utils.config import polymarket_config


# ─── Mapping helpers ────────────────────────────────────────────────

def _map_side_to_pm(side: OrderSide) -> str:
    """Convert our OrderSide to Polymarket's BUY/SELL constants."""
    return BUY if side == OrderSide.BUY else SELL


def _map_pm_status(pm_status: str) -> OrderStatus:
    """Convert Polymarket order status to our OrderStatus."""
    mapping = {
        "live": OrderStatus.OPEN,
        "matched": OrderStatus.FILLED,
        "delayed": OrderStatus.PENDING,
        "cancelled": OrderStatus.CANCELLED,
    }
    return mapping.get(pm_status.lower(), OrderStatus.PENDING)


# ─── Polymarket Connector ───────────────────────────────────────────

class PolymarketConnector(BaseConnector):
    """
    Full Polymarket integration.

    Usage:
        connector = PolymarketConnector()
        await connector.connect()

        # Get markets
        markets = await connector.get_markets(limit=10)

        # Get prices
        price = await connector.get_price(token_id, OrderSide.BUY)

        # Place a limit order (requires auth)
        order = await connector.place_order(
            market_id=token_id,
            side=OrderSide.BUY,
            order_type=OrderType.GTC,
            size=10,
            price=0.55,
        )
    """

    def __init__(self):
        super().__init__(platform_name="polymarket")
        self._clob_client: Optional[ClobClient] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._authenticated = False

    # ── Connection ───────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Connect to Polymarket APIs.

        - Always connects to Gamma/Data APIs (public, no auth).
        - If private key is configured, also authenticates with CLOB API
          for trading capabilities.
        """
        try:
            # HTTP client for Gamma and Data API calls
            self._http_client = httpx.AsyncClient(timeout=30.0)

            # Test Gamma API connectivity
            response = await self._http_client.get(
                f"{polymarket_config.gamma_url}/markets",
                params={"limit": 1},
            )
            response.raise_for_status()
            logger.info("Connected to Polymarket Gamma API (market data)")

            # Set up CLOB client if credentials are available
            if polymarket_config.has_credentials:
                self._clob_client = ClobClient(
                    host=polymarket_config.clob_url,
                    chain_id=polymarket_config.chain_id,
                    key=polymarket_config.private_key,
                    signature_type=0,  # EOA (MetaMask) = type 0
                    funder=polymarket_config.wallet_address,
                )

                # Derive API credentials (creates them if first time)
                creds = self._clob_client.create_or_derive_api_creds()
                self._clob_client.set_api_creds(creds)
                self._authenticated = True
                logger.info("Authenticated with Polymarket CLOB API (trading enabled)")
            else:
                logger.warning(
                    "No Polymarket credentials configured. "
                    "Market data available, but trading is disabled. "
                    "Set POLYMARKET_PRIVATE_KEY and POLYMARKET_WALLET_ADDRESS in .env"
                )

            self._connected = True
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to connect to Polymarket: {e}")
            return False
        except Exception as e:
            logger.error(f"Polymarket connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Close HTTP connections."""
        if self._http_client:
            await self._http_client.aclose()
        self._connected = False
        self._authenticated = False
        logger.info("Disconnected from Polymarket")

    # ── Market Data (Gamma API — public, no auth) ────────────────

    async def get_markets(self, **filters) -> list[Market]:
        """
        Fetch markets from Polymarket's Gamma API.

        Supported filters:
            limit (int): Max markets to return (default 100)
            offset (int): Pagination offset
            active (bool): Only active markets
            closed (bool): Only closed markets
            tag (str): Filter by tag (e.g., "politics", "crypto")
            keyword (str): Search term (uses 'slug' parameter)

        Returns:
            List of Market objects
        """
        self._ensure_connected()

        params = {
            "limit": filters.get("limit", 100),
            "offset": filters.get("offset", 0),
        }

        if filters.get("active") is True:
            params["active"] = "true"
        if filters.get("closed") is True:
            params["closed"] = "true"
        if "tag" in filters:
            params["tag"] = filters["tag"]

        response = await self._http_client.get(
            f"{polymarket_config.gamma_url}/markets",
            params=params,
        )
        response.raise_for_status()
        raw_markets = response.json()

        markets = []
        for m in raw_markets:
            # Each Polymarket "market" can have multiple outcomes (tokens)
            # We store the token IDs in extra for trading later
            tokens = []
            if "clobTokenIds" in m and m["clobTokenIds"]:
                # clobTokenIds is a JSON string like '["token1", "token2"]'
                import json
                try:
                    token_ids = json.loads(m["clobTokenIds"]) if isinstance(m["clobTokenIds"], str) else m["clobTokenIds"]
                    outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes", "[]"), str) else m.get("outcomes", [])
                    for i, tid in enumerate(token_ids):
                        outcome_name = outcomes[i] if i < len(outcomes) else f"Outcome {i}"
                        tokens.append({"token_id": tid, "outcome": outcome_name})
                except (json.JSONDecodeError, TypeError):
                    pass

            markets.append(Market(
                id=str(m.get("id", "")),
                name=m.get("question", m.get("title", "Unknown")),
                platform="polymarket",
                description=m.get("description", ""),
                active=m.get("active", False),
                extra={
                    "condition_id": m.get("conditionId", ""),
                    "tokens": tokens,
                    "volume": m.get("volume", 0),
                    "liquidity": m.get("liquidity", 0),
                    "end_date": m.get("endDate", ""),
                    "slug": m.get("slug", ""),
                    "image": m.get("image", ""),
                },
            ))

        logger.debug(f"Fetched {len(markets)} markets from Polymarket")
        return markets

    async def get_market(self, market_id: str) -> Market:
        """Fetch a single market by its condition ID or slug."""
        self._ensure_connected()

        response = await self._http_client.get(
            f"{polymarket_config.gamma_url}/markets/{market_id}",
        )
        response.raise_for_status()
        m = response.json()

        import json
        tokens = []
        if "clobTokenIds" in m and m["clobTokenIds"]:
            try:
                token_ids = json.loads(m["clobTokenIds"]) if isinstance(m["clobTokenIds"], str) else m["clobTokenIds"]
                outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes", "[]"), str) else m.get("outcomes", [])
                for i, tid in enumerate(token_ids):
                    outcome_name = outcomes[i] if i < len(outcomes) else f"Outcome {i}"
                    tokens.append({"token_id": tid, "outcome": outcome_name})
            except (json.JSONDecodeError, TypeError):
                pass

        return Market(
            id=str(m.get("id", "")),
            name=m.get("question", m.get("title", "Unknown")),
            platform="polymarket",
            description=m.get("description", ""),
            active=m.get("active", False),
            extra={
                "condition_id": m.get("conditionId", ""),
                "tokens": tokens,
                "volume": m.get("volume", 0),
                "liquidity": m.get("liquidity", 0),
                "end_date": m.get("endDate", ""),
                "slug": m.get("slug", ""),
            },
        )

    async def get_orderbook(self, market_id: str) -> OrderBook:
        """
        Fetch order book for a token ID.

        Note: market_id here should be a Polymarket token_id (one side of a market).
        Use market.extra["tokens"][0]["token_id"] to get this.
        """
        self._ensure_connected()

        # Use CLOB API (public endpoint, no auth needed)
        response = await self._http_client.get(
            f"{polymarket_config.clob_url}/book",
            params={"token_id": market_id},
        )
        response.raise_for_status()
        data = response.json()

        bids = [
            {"price": float(b.get("price", 0)), "size": float(b.get("size", 0))}
            for b in data.get("bids", [])
        ]
        asks = [
            {"price": float(a.get("price", 0)), "size": float(a.get("size", 0))}
            for a in data.get("asks", [])
        ]

        # Sort: bids descending (best bid first), asks ascending (best ask first)
        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])

        return OrderBook(
            market_id=market_id,
            bids=bids,
            asks=asks,
        )

    async def get_price(self, market_id: str, side: OrderSide) -> float:
        """
        Get the best available price for a token.

        Args:
            market_id: The token_id (not the market condition ID)
            side: BUY or SELL
        """
        self._ensure_connected()

        side_str = "buy" if side == OrderSide.BUY else "sell"
        response = await self._http_client.get(
            f"{polymarket_config.clob_url}/price",
            params={"token_id": market_id, "side": side_str},
        )
        response.raise_for_status()
        data = response.json()
        return float(data.get("price", 0))

    async def get_midpoint(self, market_id: str) -> float:
        """Get the midpoint price between best bid and ask."""
        self._ensure_connected()

        response = await self._http_client.get(
            f"{polymarket_config.clob_url}/midpoint",
            params={"token_id": market_id},
        )
        response.raise_for_status()
        data = response.json()
        return float(data.get("mid", 0))

    async def get_spread(self, market_id: str) -> dict:
        """Get the bid-ask spread for a token."""
        self._ensure_connected()

        response = await self._http_client.get(
            f"{polymarket_config.clob_url}/spread",
            params={"token_id": market_id},
        )
        response.raise_for_status()
        return response.json()

    # ── Polymarket-specific: Events & Discovery ──────────────────

    async def get_events(self, limit: int = 20, active: bool = True) -> list[dict]:
        """
        Fetch events from Gamma API.
        Events group related markets together (e.g., "US Election 2024"
        contains markets like "Will X win?", "Will Y win?").
        """
        self._ensure_connected()

        params = {"limit": limit}
        if active:
            params["active"] = "true"

        response = await self._http_client.get(
            f"{polymarket_config.gamma_url}/events",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def search_markets(self, query: str, limit: int = 20) -> list[Market]:
        """Search for markets by keyword."""
        self._ensure_connected()

        response = await self._http_client.get(
            f"{polymarket_config.gamma_url}/markets",
            params={"_q": query, "limit": limit, "active": "true"},
        )
        response.raise_for_status()
        raw = response.json()

        import json
        markets = []
        for m in raw:
            tokens = []
            if "clobTokenIds" in m and m["clobTokenIds"]:
                try:
                    token_ids = json.loads(m["clobTokenIds"]) if isinstance(m["clobTokenIds"], str) else m["clobTokenIds"]
                    outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes", "[]"), str) else m.get("outcomes", [])
                    for i, tid in enumerate(token_ids):
                        outcome_name = outcomes[i] if i < len(outcomes) else f"Outcome {i}"
                        tokens.append({"token_id": tid, "outcome": outcome_name})
                except (json.JSONDecodeError, TypeError):
                    pass

            markets.append(Market(
                id=str(m.get("id", "")),
                name=m.get("question", "Unknown"),
                platform="polymarket",
                active=m.get("active", False),
                extra={"tokens": tokens, "volume": m.get("volume", 0)},
            ))

        return markets

    # ── Trading (CLOB API — requires auth) ───────────────────────

    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        order_type: OrderType,
        size: float,
        price: Optional[float] = None,
    ) -> Order:
        """
        Place an order on Polymarket.

        Args:
            market_id: The token_id to trade
            side: BUY or SELL
            order_type: GTC (limit), FOK (market), MARKET
            size: Number of shares (for limit) or dollar amount (for market buy)
            price: Required for GTC/LIMIT orders (0.01 to 0.99)

        Returns:
            Order object with Polymarket order ID
        """
        self._ensure_authenticated()

        pm_side = _map_side_to_pm(side)

        if order_type in (OrderType.MARKET, OrderType.FOK):
            # Market order — size is the dollar amount to spend
            market_order = MarketOrderArgs(
                token_id=market_id,
                amount=size,
                side=pm_side,
            )
            signed_order = self._clob_client.create_market_order(market_order)
            response = self._clob_client.post_order(signed_order, PMOrderType.FOK)
        else:
            # Limit order (GTC)
            if price is None:
                raise ValueError("Price is required for limit/GTC orders")
            if not (0.01 <= price <= 0.99):
                raise ValueError(f"Price must be between 0.01 and 0.99, got {price}")

            limit_order = OrderArgs(
                token_id=market_id,
                price=price,
                size=size,
                side=pm_side,
            )
            signed_order = self._clob_client.create_order(limit_order)
            response = self._clob_client.post_order(signed_order, PMOrderType.GTC)

        logger.info(
            f"Order placed: {side.value} {size} @ {price or 'market'} "
            f"on token {market_id[:16]}... → {response}"
        )

        # Parse response into our Order model
        order_id = response.get("orderID", response.get("id", "unknown"))
        return Order(
            id=order_id,
            market_id=market_id,
            side=side,
            order_type=order_type,
            price=price or 0,
            size=size,
            status=OrderStatus.OPEN,
            platform="polymarket",
            extra={"raw_response": response},
        )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order by ID."""
        self._ensure_authenticated()

        try:
            self._clob_client.cancel(order_id)
            logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def cancel_all_orders(self) -> bool:
        """Cancel ALL open orders."""
        self._ensure_authenticated()

        try:
            self._clob_client.cancel_all()
            logger.info("Cancelled all open orders")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False

    async def get_order(self, order_id: str) -> Order:
        """Get status of a specific order."""
        self._ensure_authenticated()

        response = self._clob_client.get_order(order_id)

        return Order(
            id=response.get("id", order_id),
            market_id=response.get("asset_id", ""),
            side=OrderSide.BUY if response.get("side") == "BUY" else OrderSide.SELL,
            order_type=OrderType.GTC,
            price=float(response.get("price", 0)),
            size=float(response.get("original_size", 0)),
            filled_size=float(response.get("size_matched", 0)),
            status=_map_pm_status(response.get("status", "unknown")),
            platform="polymarket",
            extra={"raw": response},
        )

    async def get_open_orders(self, market_id: Optional[str] = None) -> list[Order]:
        """Get all open orders, optionally filtered by token ID."""
        self._ensure_authenticated()

        params = {}
        if market_id:
            params["asset_id"] = market_id

        response = self._clob_client.get_orders(**params)

        orders = []
        for o in response:
            if o.get("status", "").lower() == "live":
                orders.append(Order(
                    id=o.get("id", ""),
                    market_id=o.get("asset_id", ""),
                    side=OrderSide.BUY if o.get("side") == "BUY" else OrderSide.SELL,
                    order_type=OrderType.GTC,
                    price=float(o.get("price", 0)),
                    size=float(o.get("original_size", 0)),
                    filled_size=float(o.get("size_matched", 0)),
                    status=OrderStatus.OPEN,
                    platform="polymarket",
                ))
        return orders

    # ── Portfolio (Data API — public, uses wallet address) ───────

    async def get_positions(self) -> list[Position]:
        """
        Get current positions from the Data API.
        Uses your wallet address to look up positions (no auth needed).
        """
        self._ensure_connected()

        if not polymarket_config.wallet_address:
            logger.warning("No wallet address configured — cannot fetch positions")
            return []

        response = await self._http_client.get(
            f"{polymarket_config.data_url}/positions",
            params={"user": polymarket_config.wallet_address},
        )
        response.raise_for_status()
        raw_positions = response.json()

        positions = []
        for p in raw_positions:
            size = float(p.get("size", 0))
            if size == 0:
                continue  # Skip zero positions

            positions.append(Position(
                market_id=p.get("asset", ""),
                side=OrderSide.BUY,  # Polymarket positions are long by default
                size=size,
                entry_price=float(p.get("avgPrice", 0)),
                current_price=float(p.get("curPrice", 0)),
                platform="polymarket",
                extra={
                    "market_slug": p.get("slug", ""),
                    "title": p.get("title", ""),
                    "outcome": p.get("outcome", ""),
                    "pnl": float(p.get("pnl", 0)),
                    "cashPnl": float(p.get("cashPnl", 0)),
                },
            ))

        logger.debug(f"Found {len(positions)} active positions on Polymarket")
        return positions

    async def get_balance(self) -> dict:
        """
        Get USDC balance on Polymarket.
        Note: Polymarket uses USDC on Polygon for all trades.
        """
        self._ensure_connected()

        if not self._authenticated:
            return {"usdc": 0, "note": "Auth required for balance check"}

        # The CLOB client doesn't have a direct balance endpoint.
        # We can check via the allowance/balance endpoints.
        # For now, return position-based estimate.
        positions = await self.get_positions()
        total_value = sum(p.current_price * p.size for p in positions)

        return {
            "positions_value": round(total_value, 2),
            "num_positions": len(positions),
            "platform": "polymarket",
        }

    # ── Polymarket-specific: Trade History ────────────────────────

    async def get_trade_history(self, limit: int = 50) -> list[dict]:
        """Fetch recent trade history from the Data API."""
        self._ensure_connected()

        if not polymarket_config.wallet_address:
            return []

        response = await self._http_client.get(
            f"{polymarket_config.data_url}/activity",
            params={"user": polymarket_config.wallet_address, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    # ── Internal helpers ─────────────────────────────────────────

    def _ensure_connected(self):
        """Raise if not connected."""
        if not self._connected:
            raise ConnectionError(
                "Not connected to Polymarket. Call await connector.connect() first."
            )

    def _ensure_authenticated(self):
        """Raise if not authenticated (needed for trading)."""
        self._ensure_connected()
        if not self._authenticated:
            raise PermissionError(
                "Not authenticated with Polymarket CLOB API. "
                "Set POLYMARKET_PRIVATE_KEY and POLYMARKET_WALLET_ADDRESS in .env "
                "to enable trading."
            )
