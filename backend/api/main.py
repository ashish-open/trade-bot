"""
FastAPI application — entry point for the Trade Bot API.

Runs the paper trading engine with simulated market data.
No real API credentials needed.

Run:  uvicorn backend.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.engine.market_simulator import MarketSimulator
from backend.engine.paper_trader import PaperTradingEngine
from backend.api.dependencies import set_simulator, set_paper_engine, get_simulator
from backend.api.routes import health, portfolio, markets, orders, trades, ws

# ─── App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trade Bot API",
    version="0.1.0",
    description="Paper trading API with simulated market data",
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
    # Start the market simulator (generates live price data)
    simulator = MarketSimulator()
    simulator.start()
    set_simulator(simulator)

    # Start the paper trading engine ($10,000 starting balance)
    engine = PaperTradingEngine(simulator, starting_balance=10000.0)
    set_paper_engine(engine)

    logger.info("Market simulator started (8 simulated markets)")
    logger.info("Paper trading engine ready ($10,000 starting balance)")


@app.on_event("shutdown")
async def shutdown():
    simulator = get_simulator()
    if simulator:
        simulator.stop()
    logger.info("Shutdown complete")
