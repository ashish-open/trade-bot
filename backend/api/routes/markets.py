"""Market discovery and data endpoints."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.api.dependencies import get_simulator

router = APIRouter(tags=["markets"])


@router.get("/platforms")
async def get_platforms():
    """Get all available trading platforms with market counts."""
    sim = get_simulator()
    if not sim:
        return []
    return sim.get_platforms()


@router.get("/markets")
async def get_markets(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
):
    """Get available simulated markets, optionally filtered by platform and search."""
    sim = get_simulator()
    if not sim:
        return []
    return sim.get_markets(platform=platform or "", search=search or "", limit=limit)


@router.get("/markets/{market_id}")
async def get_market_detail(market_id: str):
    """Get detailed info for a single market."""
    sim = get_simulator()
    if not sim:
        return {"error": "Simulator not running"}
    market = sim.get_market(market_id)
    if not market:
        return {"error": "Market not found"}
    return market


@router.get("/orderbook/{market_id}")
async def get_orderbook(market_id: str):
    """Get the order book for a simulated market."""
    sim = get_simulator()
    if not sim:
        return {"bids": [], "asks": []}
    return sim.get_orderbook(market_id)


@router.get("/price/{market_id}")
async def get_price(market_id: str, side: str = "buy"):
    """Get current price for a market."""
    sim = get_simulator()
    if not sim:
        return {"price": 0}
    return {"price": sim.get_price(market_id, side)}
