"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter

from backend.api.dependencies import get_polymarket

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    polymarket = get_polymarket()
    return {
        "status": "ok",
        "polymarket_connected": polymarket.is_connected if polymarket else False,
        "timestamp": datetime.utcnow().isoformat(),
    }
