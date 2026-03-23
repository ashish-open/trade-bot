"""Market discovery and data endpoints — real data only."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.api.dependencies import get_polymarket_feed, get_data_provider

router = APIRouter(tags=["markets"])


PLATFORMS = {
    "polymarket": {"label": "Polymarket", "type": "prediction", "icon": "target"},
    "binance":    {"label": "Binance",    "type": "spot",       "icon": "coins"},
    "hyperliquid":{"label": "Hyperliquid","type": "perp",       "icon": "zap"},
}


@router.get("/platforms")
async def get_platforms():
    """Get all available trading platforms with market counts and data source."""
    feed = get_polymarket_feed()
    provider = get_data_provider()
    results = []

    for pid, meta in PLATFORMS.items():
        entry = {
            "id": pid,
            "label": meta["label"],
            "type": meta["type"],
            "icon": meta["icon"],
            "marketCount": 0,
            "dataSource": "unavailable",
        }

        if pid == "polymarket" and feed and feed.is_running():
            entry["dataSource"] = "live"
            entry["marketCount"] = len(feed.get_markets())
        elif pid in ("binance", "hyperliquid") and provider and provider.is_running():
            real_markets = provider.get_markets(platform=pid)
            entry["dataSource"] = "live"
            entry["marketCount"] = len(real_markets)

        results.append(entry)

    return results


@router.get("/markets")
async def get_markets(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
):
    """Get available markets — real data only."""
    feed = get_polymarket_feed()
    provider = get_data_provider()
    results = []

    # Polymarket (real feed)
    if not platform or platform == "polymarket":
        if feed and feed.is_running():
            poly_markets = feed.get_markets(search=search or "", limit=limit)
            for m in poly_markets:
                m["dataSource"] = "live"
            results.extend(poly_markets)

    # Binance + Hyperliquid (real crypto data)
    for plat in ["binance", "hyperliquid"]:
        if platform and platform != plat:
            continue
        if provider and provider.is_running():
            real_markets = provider.get_markets(platform=plat, search=search or "", limit=limit)
            results.extend(real_markets)

    return results[:limit]


@router.get("/markets/{market_id}")
async def get_market_detail(market_id: str):
    """Get detailed info for a single market."""
    feed = get_polymarket_feed()
    provider = get_data_provider()

    if feed and feed.is_running():
        market = feed.get_market(market_id)
        if market:
            market["dataSource"] = "live"
            return market

    if provider and provider.is_running():
        market = provider.get_market(market_id)
        if market:
            return market

    return {"error": "Market not found"}


@router.get("/orderbook/{market_id}")
async def get_orderbook(market_id: str):
    """Get order book — real from CLOB API for Polymarket, generated from real prices for crypto."""
    feed = get_polymarket_feed()
    provider = get_data_provider()

    if feed and feed.is_running():
        market = feed.get_market(market_id)
        if market:
            book = await feed.fetch_orderbook(market_id)
            if book["bids"] or book["asks"]:
                return book

    if provider and provider.is_running():
        book = provider.get_orderbook(market_id)
        if book["bids"] or book["asks"]:
            return book

    return {"bids": [], "asks": []}


@router.get("/price/{market_id}")
async def get_price(market_id: str, side: str = "buy"):
    """Get current price for a market."""
    feed = get_polymarket_feed()
    provider = get_data_provider()

    if feed and feed.is_running():
        price = feed.get_price(market_id, side)
        if price > 0:
            return {"price": price, "source": "live"}

    if provider and provider.is_running():
        price = provider.get_price(market_id, side)
        if price > 0:
            return {"price": price, "source": "live"}

    return {"price": 0, "source": "none"}
