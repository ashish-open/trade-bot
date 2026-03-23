"""Macroeconomic endpoints — indices, bonds, commodities, and market sentiment."""

from fastapi import APIRouter
from backend.api.dependencies import get_macro_provider

router = APIRouter(tags=["macro"])


@router.get("/macro/overview")
async def get_macro_overview():
    """Get full market overview with indices, bonds, commodities, and VIX."""
    provider = get_macro_provider()
    if not provider:
        return {"indices": {"all": []}, "bonds": {"yields": []}, "commodities": {"all": []}, "volatility": {}, "sentiment": "unknown"}

    return provider.get_overview()


@router.get("/macro/indices")
async def get_macro_indices():
    """Get global stock indices with prices and changes."""
    provider = get_macro_provider()
    if not provider:
        return {"indices": []}
    return {"indices": provider.get_indices()}


@router.get("/macro/treasuries")
async def get_macro_treasuries():
    """Get treasury yields (10Y, 5Y, 30Y, 13W)."""
    provider = get_macro_provider()
    if not provider:
        return {"yields": []}
    return {"yields": provider.get_treasury_yields()}


@router.get("/macro/commodities")
async def get_macro_commodities():
    """Get commodity prices (gold, silver, oil, gas)."""
    provider = get_macro_provider()
    if not provider:
        return {"commodities": []}
    return {"commodities": provider.get_commodities()}


@router.get("/macro/fear-greed")
async def get_macro_fear_greed():
    """Get VIX data and market sentiment indicator."""
    provider = get_macro_provider()
    if not provider:
        return {"vix": None, "condition": "unknown"}

    vix = provider.get_vix()
    condition = provider._assess_market_condition(vix) if vix else "unknown"
    return {"vix": vix, "condition": condition}


@router.get("/macro/{symbol_id}/history")
async def get_macro_symbol_history(symbol_id: str):
    """Get price data for any macro symbol (index, bond, commodity)."""
    provider = get_macro_provider()
    if not provider:
        return {"symbol": symbol_id, "data": None}

    # Look up in all categories
    result = provider.get_index(symbol_id)
    if not result:
        result = provider.get_yield(symbol_id)
    if not result:
        result = provider.get_commodity(symbol_id)

    return {"symbol": symbol_id, "data": result}
