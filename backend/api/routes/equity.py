"""Equity market endpoints — stocks and ETFs."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.api.dependencies import get_equity_provider

router = APIRouter(tags=["equity"])


@router.get("/equity/markets")
async def get_equity_markets(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
    sector: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
):
    """Get all tracked stocks and ETFs with optional filtering."""
    provider = get_equity_provider()
    if not provider:
        return []

    # Provider's get_markets takes (market_type, search, limit)
    # We filter by sector after — returns [] if still loading, that's fine
    markets = provider.get_markets(market_type=type or "", search=search or "", limit=limit)

    if sector:
        markets = [m for m in markets if m.get("sector", "").lower() == sector.lower()]

    for m in markets:
        m["dataSource"] = "live"

    return markets[:limit]


# Static routes BEFORE dynamic {ticker} routes
@router.get("/equity/screener")
async def get_equity_screener(
    min_market_cap: Optional[int] = Query(default=None),
    max_pe: Optional[float] = Query(default=None),
    min_dividend_yield: Optional[float] = Query(default=0.0),
    sector: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
):
    """Stock screener with financial filters."""
    provider = get_equity_provider()
    if not provider or not provider.is_running():
        return []

    results = provider.get_screener(
        min_market_cap=min_market_cap,
        max_pe=max_pe,
        min_dividend_yield=min_dividend_yield or 0.0,
        sector=sector,
    )
    return (results or [])[:limit]


@router.get("/equity/sectors")
async def get_equity_sectors():
    """Get sector breakdown and performance."""
    provider = get_equity_provider()
    if not provider or not provider.is_running():
        return {"sectors": {}}

    # Build sector summary from markets
    markets = provider.get_markets()
    sectors = {}
    for m in markets:
        s = m.get("sector", "Other")
        if s not in sectors:
            sectors[s] = {"count": 0, "total_change": 0, "stocks": []}
        sectors[s]["count"] += 1
        sectors[s]["total_change"] += m.get("change", 0)
        sectors[s]["stocks"].append(m.get("symbol", ""))

    for s in sectors:
        cnt = sectors[s]["count"]
        sectors[s]["avg_change"] = round(sectors[s]["total_change"] / cnt, 4) if cnt > 0 else 0
        del sectors[s]["total_change"]

    return {"sectors": sectors}


# Dynamic {ticker} routes
@router.get("/equity/{ticker}")
async def get_equity_quote(ticker: str):
    """Get detailed quote and fundamentals for a ticker."""
    provider = get_equity_provider()
    if not provider or not provider.is_running():
        return {"error": "Equity provider unavailable"}

    # Normalize: eq-AAPL → eq-AAPL, AAPL → eq-AAPL
    market_id = ticker if ticker.startswith("eq-") or ticker.startswith("etf-") else f"eq-{ticker}"
    market = provider.get_market(market_id)

    # Try ETF prefix if stock not found
    if not market and not ticker.startswith("etf-"):
        market = provider.get_market(f"etf-{ticker}")

    if market:
        # Add fundamentals
        raw_ticker = ticker.replace("eq-", "").replace("etf-", "")
        fund = provider.get_fundamentals(raw_ticker)
        if fund:
            market["fundamentals"] = fund
        market["dataSource"] = "live"
        return market

    return {"error": f"Ticker {ticker} not found"}


@router.get("/equity/{ticker}/history")
async def get_equity_history(ticker: str):
    """Get OHLCV price history for a ticker."""
    provider = get_equity_provider()
    if not provider or not provider.is_running():
        return {"ticker": ticker, "data": []}

    market_id = ticker if ticker.startswith("eq-") or ticker.startswith("etf-") else f"eq-{ticker}"
    history = provider.get_price_history(market_id)

    # Try ETF prefix
    if not history and not ticker.startswith("etf-"):
        history = provider.get_price_history(f"etf-{ticker}")

    return {"ticker": ticker, "data": history or []}


@router.get("/equity/{ticker}/indicators")
async def get_equity_indicators(ticker: str):
    """Get technical indicators (SMA, RSI, MACD, BB) for a ticker."""
    provider = get_equity_provider()
    if not provider or not provider.is_running():
        return {"ticker": ticker, "indicators": {}}

    market_id = ticker if ticker.startswith("eq-") or ticker.startswith("etf-") else f"eq-{ticker}"
    indicators = provider.get_indicators(market_id)

    if not indicators and not ticker.startswith("etf-"):
        indicators = provider.get_indicators(f"etf-{ticker}")

    return {"ticker": ticker, "indicators": indicators or {}}
