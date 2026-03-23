"""API routes for strategy management and market data/indicators."""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from backend.api.dependencies import get_strategy_manager, get_data_provider

router = APIRouter(tags=["strategies"])


# ─── Request Models ──────────────────────────────────────────

class RegisterStrategyRequest(BaseModel):
    key: str  # Strategy registry key (e.g. "sma_crossover")
    markets: Optional[list[str]] = None
    max_position_size: Optional[float] = None
    params: Optional[dict] = None
    enabled: Optional[bool] = None


class UpdateStrategyRequest(BaseModel):
    enabled: Optional[bool] = None
    markets: Optional[list[str]] = None
    maxPositionSize: Optional[float] = None
    params: Optional[dict] = None


# ─── Strategy Routes ─────────────────────────────────────────

@router.get("/strategies")
async def list_strategies():
    """List all registered strategies and their state."""
    mgr = get_strategy_manager()
    if not mgr:
        return []
    return mgr.list_strategies()


@router.get("/strategies/available")
async def list_available_strategies():
    """List all available strategy types (can be registered)."""
    mgr = get_strategy_manager()
    if not mgr:
        return []
    return mgr.list_available()


@router.post("/strategies/register")
async def register_strategy(req: RegisterStrategyRequest):
    """Register and activate a new strategy."""
    from backend.strategies.base import StrategyConfig

    mgr = get_strategy_manager()
    if not mgr:
        return {"error": "Strategy manager not initialized"}

    config = None
    if req.markets or req.params or req.max_position_size is not None:
        config = StrategyConfig(
            params=req.params or {},
            markets=req.markets or [],
            max_position_size=req.max_position_size or 500.0,
            enabled=req.enabled if req.enabled is not None else True,
        )

    return mgr.register_strategy(req.key, config)


@router.put("/strategies/{name}")
async def update_strategy(name: str, req: UpdateStrategyRequest):
    """Update a registered strategy's configuration."""
    mgr = get_strategy_manager()
    if not mgr:
        return {"error": "Strategy manager not initialized"}
    return mgr.update_strategy_config(name, req.model_dump(exclude_none=True))


@router.delete("/strategies/{name}")
async def unregister_strategy(name: str):
    """Remove a registered strategy."""
    mgr = get_strategy_manager()
    if not mgr:
        return {"error": "Strategy manager not initialized"}
    return mgr.unregister_strategy(name)


@router.post("/strategies/evaluate")
async def evaluate_now():
    """Force immediate evaluation of all strategies. Returns new signals."""
    mgr = get_strategy_manager()
    if not mgr:
        return {"error": "Strategy manager not initialized"}
    signals = await mgr.evaluate_now()
    return {"signals": signals, "count": len(signals)}


@router.get("/strategies/signals")
async def get_signals(limit: int = Query(default=50, le=200)):
    """Get recent strategy signals."""
    mgr = get_strategy_manager()
    if not mgr:
        return []
    return mgr.get_signals(limit)


@router.get("/strategies/executions")
async def get_executions(limit: int = Query(default=50, le=200)):
    """Get auto-executed trades from strategies."""
    mgr = get_strategy_manager()
    if not mgr:
        return []
    return mgr.get_executions(limit)


@router.get("/strategies/stats")
async def get_strategy_stats():
    """Get strategy manager statistics."""
    mgr = get_strategy_manager()
    if not mgr:
        return {}
    return mgr.get_stats()


# ─── Market Data / Indicators ─────────────────────────────────

@router.get("/indicators/{market_id}")
async def get_indicators(market_id: str):
    """Get technical indicators (SMA, RSI, MACD, BB) for a market."""
    provider = get_data_provider()
    if not provider:
        return {"error": "Data provider not initialized"}
    indicators = provider.get_indicators(market_id)
    if not indicators:
        return {"error": f"No indicators available for {market_id}"}
    return indicators


@router.get("/indicators")
async def get_all_indicators():
    """Get indicators for all markets."""
    provider = get_data_provider()
    if not provider:
        return {}
    return provider.get_all_indicators()


@router.get("/history/{market_id}")
async def get_price_history(market_id: str):
    """Get historical price data for a market."""
    provider = get_data_provider()
    if not provider:
        return []
    return provider.get_price_history(market_id)
