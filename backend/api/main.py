"""
FastAPI application — entry point for the Trade Bot API.

Hybrid mode:
- Polymarket: Real market data from Gamma/CLOB APIs (falls back to simulated)
- Binance: Simulated spot prices
- Hyperliquid: Simulated perp prices

Run:  uvicorn backend.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.engine.market_simulator import MarketSimulator
from backend.engine.paper_trader import PaperTradingEngine
from backend.connectors.polymarket_feed import PolymarketFeed
from backend.api.dependencies import (
    set_simulator, set_paper_engine, set_polymarket_feed,
    get_simulator, get_polymarket_feed,
)
from backend.api.routes import health, portfolio, markets, orders, trades, ws

# ─── App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trade Bot API",
    version="0.2.0",
    description="Multi-platform paper trading with real Polymarket data",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───────────────────────────────────────────

app.include_router(health.router,     prefix="/api")
app.include_router(portfolio.router,  prefix="/api")
app.include_router(markets.router,    prefix="/api")
app.include_router(orders.router,     prefix="/api")
app.include_router(trades.router,     prefix="/api")
app.include_router(ws.router)

# ─── Lifecycle ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # 1) Start simulated markets (Binance + Hyperliquid + fallback Polymarket)
    simulator = MarketSimulator()
    simulator.start()
    set_simulator(simulator)
    logger.info(f"Market simulator started ({len(simulator.markets)} simulated markets)")

    # 2) Try to start real Polymarket feed
    feed = PolymarketFeed(refresh_interval=15)
    try:
        await feed.start()
        if feed.is_running():
            set_polymarket_feed(feed)
            logger.info(f"Polymarket LIVE feed active — {len(feed.get_markets())} real markets")
        else:
            logger.warning("Polymarket feed started but no markets loaded — using simulated data")
    except Exception as e:
        logger.warning(f"Polymarket live feed unavailable ({e}) — using simulated data")

    # 3) Start paper trading engine
    engine = PaperTradingEngine(simulator, starting_balance=10000.0)
    set_paper_engine(engine)
    logger.info("Paper trading engine ready ($10,000 starting balance)")


@app.on_event("shutdown")
async def shutdown():
    simulator = get_simulator()
    if simulator:
        simulator.stop()

    feed = get_polymarket_feed()
    if feed:
        await feed.stop()

    logger.info("Shutdown complete")
