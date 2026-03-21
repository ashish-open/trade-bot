"""
FastAPI application — entry point for the Trade Bot API.

Registers all route modules and manages startup/shutdown lifecycle.

Run:  uvicorn backend.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.connectors.polymarket import PolymarketConnector
from backend.api.dependencies import set_polymarket, get_polymarket
from backend.api.routes import health, portfolio, markets, orders, trades, ws

# ─── App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trade Bot API",
    version="0.1.0",
    description="Backend API for the Trade Bot dashboard",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
app.include_router(ws.router)  # WebSocket has no /api prefix

# ─── Lifecycle ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    connector = PolymarketConnector()
    connected = await connector.connect()
    set_polymarket(connector)

    if connected:
        logger.info("Polymarket connector initialized")
    else:
        logger.warning("Polymarket connector failed — running in offline mode")


@app.on_event("shutdown")
async def shutdown():
    connector = get_polymarket()
    if connector:
        await connector.disconnect()
