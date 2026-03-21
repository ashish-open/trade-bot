"""WebSocket endpoint for real-time dashboard updates."""

import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from backend.api.dependencies import get_simulator, get_paper_engine, get_polymarket_feed

router = APIRouter()
ws_connections: set[WebSocket] = set()


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """
    Push real-time updates every second:
    - Market prices (real Polymarket + simulated others)
    - Portfolio value and positions
    - Limit order fill checks
    """
    await websocket.accept()
    ws_connections.add(websocket)
    logger.info(f"WebSocket connected ({len(ws_connections)} clients)")

    try:
        while True:
            sim = get_simulator()
            engine = get_paper_engine()
            feed = get_polymarket_feed()

            update = {"type": "tick", "timestamp": datetime.utcnow().isoformat()}

            market_updates = []

            # Real Polymarket data (if feed is live)
            if feed and feed.is_running():
                for m in feed.get_markets():
                    market_updates.append({
                        "id": m["id"],
                        "price": m["price"],
                        "change": m.get("change", 0),
                        "platform": "polymarket",
                        "dataSource": "live",
                    })

            # Simulated markets (Binance + Hyperliquid + fallback Polymarket)
            if sim:
                live_poly_ids = {m["id"] for m in market_updates}
                for m_id, m in sim.markets.items():
                    # Skip simulated Polymarket if live feed covers it
                    if m.platform == "polymarket" and live_poly_ids:
                        continue
                    decimals = 4 if m.market_type == "prediction" else 2
                    market_updates.append({
                        "id": m_id,
                        "price": round(m.true_price, decimals),
                        "change": m.get_price_change(),
                        "platform": m.platform,
                        "dataSource": "simulated",
                    })

            update["markets"] = market_updates

            if engine:
                engine.check_fills()
                portfolio = engine.get_portfolio()
                update["portfolio"] = {
                    "totalValue": portfolio["totalValue"],
                    "cash": portfolio["cash"],
                    "totalPnl": portfolio["totalPnl"],
                    "totalPnlPercent": portfolio["totalPnlPercent"],
                    "dayPnl": portfolio["dayPnl"],
                    "dayPnlPercent": portfolio["dayPnlPercent"],
                    "winRate": portfolio["winRate"],
                    "totalTrades": portfolio["totalTrades"],
                    "openPositions": portfolio["openPositions"],
                }
                update["positions"] = portfolio["positions"]

            await websocket.send_json(update)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        ws_connections.discard(websocket)
        logger.info(f"WebSocket disconnected ({len(ws_connections)} clients)")
    except Exception as e:
        ws_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
