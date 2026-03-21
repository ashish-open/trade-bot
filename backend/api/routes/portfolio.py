"""Portfolio and positions endpoints."""

from fastapi import APIRouter
from backend.api.dependencies import get_paper_engine

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio")
async def get_portfolio():
    """Get full portfolio summary (value, P&L, cash, positions count)."""
    engine = get_paper_engine()
    if not engine:
        return {"error": "Paper trading engine not running"}

    engine.check_fills()  # Check for limit order fills
    return engine.get_portfolio()


@router.get("/positions")
async def get_positions():
    """Get all open positions with real-time P&L."""
    engine = get_paper_engine()
    if not engine:
        return []

    engine.check_fills()
    return engine.get_positions()
