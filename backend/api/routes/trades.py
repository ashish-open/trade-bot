"""Trade history endpoints."""

from fastapi import APIRouter, Query
from backend.api.dependencies import get_paper_engine

router = APIRouter(tags=["trades"])


@router.get("/trades")
async def get_trade_history(limit: int = Query(default=50, le=200)):
    """Get recent completed trades."""
    engine = get_paper_engine()
    if not engine:
        return []
    return engine.get_trade_history(limit=limit)
