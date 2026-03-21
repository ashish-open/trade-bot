"""Trade history endpoints."""

from fastapi import APIRouter, Query

from backend.api.dependencies import get_polymarket

router = APIRouter(tags=["trades"])


@router.get("/trades")
async def get_trade_history(limit: int = Query(default=50, le=200)):
    """Get recent trade history."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return []

    trades = await polymarket.get_trade_history(limit=limit)
    return trades
