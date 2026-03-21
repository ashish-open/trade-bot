"""WebSocket endpoint for real-time dashboard updates."""

import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from backend.api.dependencies import get_polymarket

router = APIRouter()

# Track active WebSocket connections
ws_connections: set[WebSocket] = set()


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Pushes portfolio/position/price updates every few seconds.
    """
    await websocket.accept()
    ws_connections.add(websocket)
    logger.info(f"WebSocket client connected ({len(ws_connections)} total)")

    try:
        while True:
            update = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
            }

            polymarket = get_polymarket()
            if polymarket and polymarket.is_connected:
                try:
                    positions = await polymarket.get_positions()
                    update["type"] = "positions_update"
                    update["positions"] = [
                        {
                            "market": p.extra.get("title", p.market_id[:30]),
                            "pnl": round(p.unrealized_pnl, 2),
                            "currentPrice": p.current_price,
                        }
                        for p in positions
                    ]
                except Exception as e:
                    update["error"] = str(e)

            await websocket.send_json(update)
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        ws_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected ({len(ws_connections)} remaining)")
    except Exception as e:
        ws_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
