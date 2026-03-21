"""Market discovery and data endpoints — hybrid real + simulated."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.api.dependencies import get_simulator, get_polymarket_feed

router = APIRouter(tags=["markets"])


def _poly_feed_active() -> bool:
    feed = get_polymarket_feed()
    return feed is not None and feed.is_running()


@router.get("/platforms")
async def get_platforms():
    """Get all available trading platforms with market counts and data source."""
    sim = get_simulator()
    feed = get_polymarket_feed()
    if not sim:
        return []

    platforms = sim.get_platforms()

    # Annotate each platform with its data source
    for p in platforms:
        if p["id"] == "polymarket" and feed and feed.is_running():
            real_count = len(feed.get_markets())
            p["dataSource"] = "live"
            p["marketCount"] = real_count
        else:
            p["dataSource"] = "simulated"

    return platforms


@router.get("/markets")
async def get_markets(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
):
    """
    Get available markets — real Polymarket data when available, simulated otherwise.
    """
    sim = get_simulator()
    feed = get_polymarket_feed()
    results = []

    # If requesting Polymarket (or all) and live feed is available
    if feed and feed.is_running() and (not platform or platform == "polymarket"):
        poly_markets = feed.get_markets(search=search or "", limit=limit)
        # Add a dataSource flag to each market
        for m in poly_markets:
            m["dataSource"] = "live"
        results.extend(poly_markets)

    # If requesting Polymarket but feed is down, use simulated
    if not results and (not platform or platform == "polymarket"):
        if sim:
            sim_poly = sim.get_markets(platform="polymarket", search=search or "", limit=limit)
            for m in sim_poly:
                m["dataSource"] = "simulated"
            results.extend(sim_poly)

    # Add other platforms (always simulated for now)
    if sim and platform != "polymarket":
        for plat in ["binance", "hyperliquid"]:
            if platform and platform != plat:
                continue
            sim_markets = sim.get_markets(platform=plat, search=search or "", limit=limit)
            for m in sim_markets:
                m["dataSource"] = "simulated"
            results.extend(sim_markets)

    return results[:limit]


@router.get("/markets/{market_id}")
async def get_market_detail(market_id: str):
    """Get detailed info for a single market (real or simulated)."""
    feed = get_polymarket_feed()
    sim = get_simulator()

    # Try live feed first
    if feed and feed.is_running():
        market = feed.get_market(market_id)
        if market:
            market["dataSource"] = "live"
            return market

    # Fall back to simulator
    if sim:
        market = sim.get_market(market_id)
        if market:
            market["dataSource"] = "simulated"
            return market

    return {"error": "Market not found"}


@router.get("/orderbook/{market_id}")
async def get_orderbook(market_id: str):
    """Get order book — real from CLOB API for Polymarket, simulated for others."""
    feed = get_polymarket_feed()
    sim = get_simulator()

    # Try real orderbook for Polymarket markets
    if feed and feed.is_running():
        market = feed.get_market(market_id)
        if market:
            book = await feed.fetch_orderbook(market_id)
            if book["bids"] or book["asks"]:
                return book

    # Fall back to simulated
    if sim:
        return sim.get_orderbook(market_id)

    return {"bids": [], "asks": []}


@router.get("/price/{market_id}")
async def get_price(market_id: str, side: str = "buy"):
    """Get current price for a market."""
    feed = get_polymarket_feed()
    sim = get_simulator()

    # Try live feed
    if feed and feed.is_running():
        price = feed.get_price(market_id, side)
        if price > 0:
            return {"price": price, "source": "live"}

    # Fall back
    if sim:
        return {"price": sim.get_price(market_id, side), "source": "simulated"}

    return {"price": 0, "source": "none"}
