"""Portfolio and positions endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import get_polymarket

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio")
async def get_portfolio():
    """Get portfolio summary stats."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return {"error": "Not connected to Polymarket"}

    positions = await polymarket.get_positions()
    balance = await polymarket.get_balance()

    total_pnl = sum(p.unrealized_pnl for p in positions)
    total_value = sum(p.current_price * p.size for p in positions)

    return {
        "totalValue": round(total_value, 2),
        "totalPnl": round(total_pnl, 2),
        "totalPnlPercent": round((total_pnl / max(total_value - total_pnl, 1)) * 100, 2),
        "openPositions": len(positions),
        "balance": balance,
    }


@router.get("/positions")
async def get_positions():
    """Get all open positions."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket.is_connected:
        return []

    positions = await polymarket.get_positions()
    return [
        {
            "id": p.market_id[:16],
            "market": p.extra.get("title", p.market_id[:30]),
            "platform": p.platform,
            "side": p.side.value.upper(),
            "size": p.size,
            "entryPrice": p.entry_price,
            "currentPrice": p.current_price,
            "pnl": round(p.unrealized_pnl, 2),
            "pnlPercent": round(p.pnl_percent, 2),
        }
        for p in positions
    ]
