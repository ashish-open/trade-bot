"""WebSocket endpoint for real-time dashboard updates."""

import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from backend.api.dependencies import get_simulator, get_paper_engine

router = APIRouter()
ws_connections: set[WebSocket] = set()


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """
    Push real-time updates to the dashboard every second:
    - Market prices (all markets, with platform info)
    - Portfolio value
    - Position P&L
    - Open order fill checks
    """
    await websocket.accept()
    ws_connections.add(websocket)
    logger.info(f"WebSocket connected ({len(ws_connections)} clients)")

    try:
        while True:
            sim = get_simulator()
            engine = get_paper_engine()

            update = {"type": "tick", "timestamp": datetime.utcnow().isoformat()}

            if sim:
                update["markets"] = [
                    {
                        "id": m_id,
                        "price": round(m.true_price, 4 if m.market_type == "prediction" else 2),
                        "change": m.get_price_change(),
                        "bid": m.get_bid_price(),
                        "ask": m.get_ask_price(),
                        "platform": m.platform,
                    }
                    for m_id, m in sim.markets.items()
                ]

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
