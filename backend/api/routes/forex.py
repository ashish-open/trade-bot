"""Forex market endpoints — currency pairs and technical analysis."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.api.dependencies import get_forex_provider

router = APIRouter(tags=["forex"])


# Static routes BEFORE dynamic routes
@router.get("/forex/pairs")
async def get_forex_pairs(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
):
    """Get all tracked forex pairs."""
    provider = get_forex_provider()
    if not provider:
        return []

    pairs = provider.get_markets(search=search or "", limit=limit)
    for p in pairs:
        p["dataSource"] = "live"
    return pairs[:limit]


@router.get("/forex/heatmap")
async def get_forex_heatmap():
    """Get all pairs with change data for correlation heatmap."""
    provider = get_forex_provider()
    if not provider:
        return {"pairs": []}

    # Build heatmap from all markets
    pairs = provider.get_markets()
    heatmap = []
    for p in pairs:
        heatmap.append({
            "id": p["id"],
            "symbol": p.get("symbol", ""),
            "price": p.get("price", 0),
            "change": p.get("change", 0),
        })
    return {"pairs": heatmap}


# Dynamic {pair_id} routes
@router.get("/forex/{pair_id}")
async def get_forex_pair_quote(pair_id: str):
    """Get detailed quote for a forex pair."""
    provider = get_forex_provider()
    if not provider or not provider.is_running():
        return {"error": "Forex provider unavailable"}

    market = provider.get_market(pair_id)
    if market:
        market["dataSource"] = "live"
        return market
    return {"error": f"Pair {pair_id} not found"}


@router.get("/forex/{pair_id}/history")
async def get_forex_history(pair_id: str):
    """Get price history for a forex pair."""
    provider = get_forex_provider()
    if not provider or not provider.is_running():
        return {"pair": pair_id, "data": []}

    history = provider.get_price_history(pair_id)
    return {"pair": pair_id, "data": history or []}


@router.get("/forex/{pair_id}/indicators")
async def get_forex_indicators(pair_id: str):
    """Get technical indicators for a forex pair."""
    provider = get_forex_provider()
    if not provider or not provider.is_running():
        return {"pair": pair_id, "indicators": {}}

    indicators = provider.get_indicators(pair_id)
    return {"pair": pair_id, "indicators": indicators or {}}
