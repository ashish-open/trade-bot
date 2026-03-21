"""Order management — place, cancel, list paper orders."""

from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from backend.api.dependencies import get_paper_engine, get_polymarket_feed, get_simulator

router = APIRouter(tags=["orders"])


class PlaceOrderRequest(BaseModel):
    market_id: str
    side: str               # "buy" or "sell"
    order_type: str = "market"  # "market" or "limit"
    size: float
    price: Optional[float] = None


@router.post("/orders")
async def place_order(req: PlaceOrderRequest):
    """Place a paper trade order (works with both real and simulated markets)."""
    engine = get_paper_engine()
    if not engine:
        return {"error": "Paper trading engine not running"}

    # For live Polymarket markets, we need to register them in the simulator
    # so the paper engine can track prices
    feed = get_polymarket_feed()
    sim = get_simulator()
    if feed and feed.is_running() and sim:
        live_market = feed.get_market(req.market_id)
        if live_market and req.market_id not in sim.markets:
            # Create a simulated market entry that mirrors the live price
            # This lets the paper engine track it
            from backend.engine.market_simulator import SimulatedMarket
            sim.markets[req.market_id] = SimulatedMarket(
                id=req.market_id,
                name=live_market["name"],
                platform="polymarket",
                market_type="prediction",
                symbol=live_market.get("symbol", ""),
                true_price=live_market["price"],
                volatility=0,  # No simulated movement — real feed updates it
                drift=0,
            )

    # Update live market prices in the simulator before placing order
    if feed and feed.is_running() and sim:
        live_market = feed.get_market(req.market_id)
        if live_market and req.market_id in sim.markets:
            sim.markets[req.market_id].true_price = live_market["price"]

    result = engine.place_order(
        market_id=req.market_id,
        side=req.side,
        order_type=req.order_type,
        size=req.size,
        price=req.price or 0,
    )
    return result


@router.get("/orders")
async def get_open_orders():
    """Get all open (unfilled) limit orders."""
    engine = get_paper_engine()
    if not engine:
        return []

    # Sync live prices before checking fills
    _sync_live_prices()
    engine.check_fills()
    return engine.get_open_orders()


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an open limit order."""
    engine = get_paper_engine()
    if not engine:
        return {"error": "Engine not running"}
    return engine.cancel_order(order_id)


def _sync_live_prices():
    """Update simulator with latest live Polymarket prices."""
    feed = get_polymarket_feed()
    sim = get_simulator()
    if not feed or not feed.is_running() or not sim:
        return
    for m in feed.get_markets():
        mid = m["id"]
        if mid in sim.markets:
            sim.markets[mid].true_price = m["price"]
