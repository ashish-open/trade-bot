"""
FastAPI application — entry point for the Trade Bot API.

v0.5.0 — Elite Trading Terminal
Real data only across all asset classes:
- Polymarket: Real prediction market data from Gamma/CLOB APIs
- Crypto: Real prices via yfinance (Binance spot + Hyperliquid perp)
- Equities: Real stock & ETF prices, fundamentals, screener
- Forex: Real FX pair prices and technicals
- Macro: Global indices, treasury yields, commodities, VIX
- Strategies: Pluggable strategy framework with auto-execution

Run:  python3 -m uvicorn backend.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.engine.paper_trader import PaperTradingEngine
from backend.connectors.polymarket_feed import PolymarketFeed
from backend.data.openbb_provider import OpenBBDataProvider
from backend.data.equity_provider import EquityDataProvider
from backend.data.forex_provider import ForexDataProvider
from backend.data.macro_provider import MacroDataProvider
from backend.strategies.manager import StrategyManager
from backend.api.dependencies import (
    set_paper_engine, set_polymarket_feed,
    set_data_provider, set_strategy_manager,
    set_equity_provider, set_forex_provider, set_macro_provider,
    get_polymarket_feed, get_data_provider, get_strategy_manager,
    get_equity_provider, get_forex_provider, get_macro_provider,
)
from backend.api.routes import health, portfolio, markets, orders, trades, ws
from backend.api.routes import strategies as strategies_routes
from backend.api.routes import equity as equity_routes
from backend.api.routes import forex as forex_routes
from backend.api.routes import macro as macro_routes

# ─── App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trade Bot — Elite Terminal",
    version="0.5.0",
    description="Multi-asset trading terminal with real data: crypto, equities, forex, macro",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───────────────────────────────────────────

app.include_router(health.router,              prefix="/api")
app.include_router(portfolio.router,           prefix="/api")
app.include_router(markets.router,             prefix="/api")
app.include_router(orders.router,              prefix="/api")
app.include_router(trades.router,              prefix="/api")
app.include_router(strategies_routes.router,   prefix="/api")
app.include_router(equity_routes.router,       prefix="/api")
app.include_router(forex_routes.router,        prefix="/api")
app.include_router(macro_routes.router,        prefix="/api")
app.include_router(ws.router)

# ─── Lifecycle ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # 1) Start real Polymarket feed
    feed = PolymarketFeed(refresh_interval=15)
    try:
        await feed.start()
        if feed.is_running():
            set_polymarket_feed(feed)
            logger.info(f"Polymarket LIVE feed active — {len(feed.get_markets())} real markets")
        else:
            logger.warning("Polymarket feed started but no markets loaded")
    except Exception as e:
        logger.warning(f"Polymarket live feed unavailable ({e})")

    # 2) Start OpenBB data provider for real crypto prices
    data_provider = OpenBBDataProvider(refresh_interval=30)
    data_provider.start()
    set_data_provider(data_provider)
    logger.info("OpenBB data provider started (real crypto prices)")

    # 3) Start Equity data provider
    equity_provider = EquityDataProvider(refresh_interval=30)
    equity_provider.start()
    set_equity_provider(equity_provider)
    logger.info("Equity data provider started (20 stocks + 10 ETFs)")

    # 4) Start Forex data provider
    forex_provider = ForexDataProvider(refresh_interval=30)
    forex_provider.start()
    set_forex_provider(forex_provider)
    logger.info("Forex data provider started (10 major pairs)")

    # 5) Start Macro data provider
    macro_provider = MacroDataProvider(refresh_interval=60)
    macro_provider.start()
    set_macro_provider(macro_provider)
    logger.info("Macro data provider started (indices, bonds, commodities, VIX)")

    # 6) Create unified price lookup that checks all real data sources
    def unified_price_fn(market_id: str, side: str) -> float:
        """Look up price from any real data source."""
        # Try Polymarket first
        pm_feed = get_polymarket_feed()
        if pm_feed and pm_feed.is_running():
            price = pm_feed.get_price(market_id, side)
            if price > 0:
                return price
        # Try OpenBB crypto data
        dp = get_data_provider()
        if dp and dp.is_running():
            price = dp.get_price(market_id, side)
            if price > 0:
                return price
        # Try Equity
        eq = get_equity_provider()
        if eq and eq.is_running():
            price = eq.get_price(market_id, side)
            if price > 0:
                return price
        # Try Forex
        fx = get_forex_provider()
        if fx and fx.is_running():
            price = fx.get_price(market_id, side)
            if price > 0:
                return price
        return 0.0

    def unified_market_info_fn(market_id: str) -> dict:
        """Look up market info from any real data source."""
        pm_feed = get_polymarket_feed()
        if pm_feed and pm_feed.is_running():
            info = pm_feed.get_market(market_id)
            if info:
                return info
        dp = get_data_provider()
        if dp and dp.is_running():
            info = dp.get_market(market_id)
            if info:
                return info
        eq = get_equity_provider()
        if eq and eq.is_running():
            info = eq.get_market(market_id)
            if info:
                return info
        fx = get_forex_provider()
        if fx and fx.is_running():
            info = fx.get_market(market_id)
            if info:
                return info
        return {}

    # 7) Start paper trading engine (uses real prices only)
    engine = PaperTradingEngine(
        price_fn=unified_price_fn,
        market_info_fn=unified_market_info_fn,
        starting_balance=10000.0,
    )
    set_paper_engine(engine)
    logger.info("Paper trading engine ready ($10,000 starting balance) — all asset classes")

    # 8) Start strategy manager with default strategies
    strategy_mgr = StrategyManager(
        data_provider=data_provider,
        paper_engine=engine,
        eval_interval=60.0,
    )
    strategy_mgr.register_strategy("sma_crossover")
    strategy_mgr.register_strategy("rsi_reversion")
    strategy_mgr.start()
    set_strategy_manager(strategy_mgr)
    logger.info("Strategy manager started with SMA Crossover + RSI Mean Reversion")

    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Trade Bot Elite Terminal v0.5.0 — All Systems GO")
    logger.info("═══════════════════════════════════════════════════")


@app.on_event("shutdown")
async def shutdown():
    feed = get_polymarket_feed()
    if feed:
        await feed.stop()

    for getter in [get_data_provider, get_equity_provider, get_forex_provider, get_macro_provider]:
        provider = getter()
        if provider:
            provider.stop()

    mgr = get_strategy_manager()
    if mgr:
        mgr.stop()

    logger.info("Shutdown complete")
