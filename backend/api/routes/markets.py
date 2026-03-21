"""Market discovery and data endpoints."""

from typing import Optional
from fastapi import APIRouter, Query

from backend.connectors.base import OrderSide
from backend.api.dependencies import get_polymarket

router = APIRouter(tags=["markets"])


@router.get("/markets")
async def get_markets(
    limit: int = Query(default=20, le=100),
    search: Optional[str] = Query(default=None),
):
    """Get available markets, optionally filtered by search term."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return []

    if search:
        markets = await polymarket.search_markets(search, limit=limit)
    else:
        markets = await polymarket.get_markets(limit=limit, active=True)

    results = []
    for m in markets:
        tokens = m.extra.get("tokens", [])
        price = 0
        if tokens:
            try:
                price = await polymarket.get_price(tokens[0]["token_id"], OrderSide.BUY)
            except Exception:
                pass

        results.append({
            "id": m.id,
            "name": m.name,
            "price": price,
            "change": 0,
            "volume": m.extra.get("volume", "0"),
            "tokens": tokens,
        })

    return results


@router.get("/markets/{market_id}")
async def get_market_detail(market_id: str):
    """Get detailed info for a single market."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return {"error": "Not connected"}

    market = await polymarket.get_market(market_id)
    return {
        "id": market.id,
        "name": market.name,
        "description": market.description,
        "active": market.active,
        "tokens": market.extra.get("tokens", []),
        "volume": market.extra.get("volume", 0),
        "endDate": market.extra.get("end_date", ""),
    }


@router.get("/orderbook/{token_id}")
async def get_orderbook(token_id: str):
    """Get the order book for a specific token."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return {"bids": [], "asks": []}

    book = await polymarket.get_orderbook(token_id)
    return {
        "bids": book.bids,
        "asks": book.asks,
        "bestBid": book.best_bid,
        "bestAsk": book.best_ask,
        "spread": book.spread,
    }
