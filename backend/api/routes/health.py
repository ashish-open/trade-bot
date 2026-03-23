"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter
from backend.api.dependencies import (
    get_paper_engine, get_data_provider, get_polymarket_feed,
    get_strategy_manager, get_equity_provider, get_forex_provider, get_macro_provider,
)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    engine = get_paper_engine()
    provider = get_data_provider()
    feed = get_polymarket_feed()
    mgr = get_strategy_manager()
    equity = get_equity_provider()
    forex = get_forex_provider()
    macro = get_macro_provider()

    return {
        "status": "ok",
        "version": "0.5.0",
        "mode": "paper",
        "providers": {
            "crypto": provider is not None and provider.is_running(),
            "polymarket": feed is not None and feed.is_running(),
            "equity": equity is not None and equity.is_running(),
            "forex": forex is not None and forex.is_running(),
            "macro": macro is not None and macro.is_running(),
        },
        "strategy_manager_active": mgr is not None and mgr._running,
        "balance": engine.cash if engine else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
