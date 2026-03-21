"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter
from backend.api.dependencies import get_simulator, get_paper_engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    sim = get_simulator()
    engine = get_paper_engine()
    return {
        "status": "ok",
        "mode": "paper",
        "simulator_running": sim is not None and sim._running,
        "markets_count": len(sim.markets) if sim else 0,
        "balance": engine.cash if engine else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
