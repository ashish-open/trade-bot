"""
Tests for the Polymarket connector.

These tests verify the connector logic without hitting the real API.
They use mock responses to simulate Polymarket's behavior.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.connectors.base import (
    Market, OrderBook, Order, Position,
    OrderSide, OrderType, OrderStatus,
)
from backend.connectors.polymarket import PolymarketConnector, _map_side_to_pm, _map_pm_status


class TestDataModels:
    """Test the shared data models."""

    def test_orderbook_best_bid_ask(self):
        book = OrderBook(
            market_id="test",
            bids=[{"price": 0.65, "size": 100}, {"price": 0.63, "size": 50}],
            asks=[{"price": 0.67, "size": 80}, {"price": 0.70, "size": 30}],
        )
        assert book.best_bid == 0.65
        assert book.best_ask == 0.67
        assert book.spread == pytest.approx(0.02)

    def test_orderbook_empty(self):
        book = OrderBook(market_id="test", bids=[], asks=[])
        assert book.best_bid is None
        assert book.best_ask is None
        assert book.spread is None

    def test_position_pnl_buy(self):
        pos = Position(
            market_id="test",
            side=OrderSide.BUY,
            size=100,
            entry_price=0.50,
            current_price=0.65,
        )
        # Bought at 0.50, now 0.65 → profit of 0.15 per share × 100 = 15.0
        assert pos.unrealized_pnl == pytest.approx(15.0)
        assert pos.pnl_percent == pytest.approx(30.0)

    def test_position_pnl_sell(self):
        pos = Position(
            market_id="test",
            side=OrderSide.SELL,
            size=50,
            entry_price=0.80,
            current_price=0.60,
        )
        # Sold at 0.80, now 0.60 → profit of 0.20 per share × 50 = 10.0
        assert pos.unrealized_pnl == pytest.approx(10.0)

    def test_position_pnl_loss(self):
        pos = Position(
            market_id="test",
            side=OrderSide.BUY,
            size=100,
            entry_price=0.70,
            current_price=0.55,
        )
        # Bought at 0.70, now 0.55 → loss of -15.0
        assert pos.unrealized_pnl == pytest.approx(-15.0)
        assert pos.pnl_percent == pytest.approx(-21.43, abs=0.01)


class TestMappingHelpers:
    """Test the Polymarket-specific mapping functions."""

    def test_map_side_buy(self):
        from py_clob_client.order_builder.constants import BUY
        assert _map_side_to_pm(OrderSide.BUY) == BUY

    def test_map_side_sell(self):
        from py_clob_client.order_builder.constants import SELL
        assert _map_side_to_pm(OrderSide.SELL) == SELL

    def test_map_status(self):
        assert _map_pm_status("live") == OrderStatus.OPEN
        assert _map_pm_status("matched") == OrderStatus.FILLED
        assert _map_pm_status("cancelled") == OrderStatus.CANCELLED
        assert _map_pm_status("delayed") == OrderStatus.PENDING
        assert _map_pm_status("unknown_status") == OrderStatus.PENDING


class TestConnectorInit:
    """Test connector initialization (no network)."""

    def test_creates_with_defaults(self):
        connector = PolymarketConnector()
        assert connector.platform_name == "polymarket"
        assert connector.is_connected is False
        assert connector._authenticated is False

    def test_ensure_connected_raises(self):
        connector = PolymarketConnector()
        with pytest.raises(ConnectionError, match="Not connected"):
            connector._ensure_connected()

    def test_ensure_authenticated_raises(self):
        connector = PolymarketConnector()
        connector._connected = True  # Fake connection
        with pytest.raises(PermissionError, match="Not authenticated"):
            connector._ensure_authenticated()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
