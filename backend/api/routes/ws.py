"""WebSocket endpoint for real-time dashboard updates."""

import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from backend.api.dependencies import (
    get_paper_engine, get_polymarket_feed,
    get_data_provider, get_strategy_manager,
    get_equity_provider, get_forex_provider, get_macro_provider,
)

router = APIRouter()
ws_connections: set[WebSocket] = set()


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """
    Push real-time updates every second:
    - Market prices (Polymarket + crypto + equity + forex)
    - Global indices and macro overview
    - Portfolio value and positions
    - Strategy signals and stats
    """
    await websocket.accept()
    ws_connections.add(websocket)
    logger.info(f"WebSocket connected ({len(ws_connections)} clients)")

    try:
        while True:
            engine = get_paper_engine()
            feed = get_polymarket_feed()
            provider = get_data_provider()
            strategy_mgr = get_strategy_manager()
            equity = get_equity_provider()
            forex = get_forex_provider()
            macro = get_macro_provider()

            update = {"type": "tick", "timestamp": datetime.utcnow().isoformat()}

            market_updates = []

            # Real Polymarket data
            if feed and feed.is_running():
                for m in feed.get_markets():
                    market_updates.append({
                        "id": m["id"],
                        "price": m["price"],
                        "change": m.get("change", 0),
                        "platform": "polymarket",
                        "dataSource": "live",
                    })

            # Real crypto data (Binance + Hyperliquid)
            if provider and provider.is_running():
                for m in provider.get_markets():
                    market_updates.append({
                        "id": m["id"],
                        "price": m["price"],
                        "change": m.get("change", 0),
                        "platform": m["platform"],
                        "dataSource": "live",
                    })

            # Real equity data
            if equity and equity.is_running():
                for m in equity.get_markets():
                    market_updates.append({
                        "id": m["id"],
                        "price": m["price"],
                        "change": m.get("change", 0),
                        "platform": "equity",
                        "dataSource": "live",
                        "type": m.get("marketType", "stock"),
                    })

            # Real forex data
            if forex and forex.is_running():
                for m in forex.get_markets():
                    market_updates.append({
                        "id": m["id"],
                        "price": m["price"],
                        "change": m.get("change", 0),
                        "platform": "forex",
                        "dataSource": "live",
                    })

            update["markets"] = market_updates

            # Macro overview (indices, bonds, commodities, VIX)
            if macro and macro.is_running():
                try:
                    overview = macro.get_overview()
                    update["macro"] = overview
                except Exception:
                    pass

            # Portfolio
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

            # Strategy info
            if strategy_mgr:
                stats = strategy_mgr.get_stats()
                update["strategies"] = {
                    "activeStrategies": stats["active_strategies"],
                    "totalSignals": stats["total_signals"],
                    "totalExecutions": stats["total_executions"],
                    "lastEvalAt": stats["last_eval_at"],
                    "recentSignals": strategy_mgr.get_signals(5),
                    "recentExecutions": strategy_mgr.get_executions(5),
                }

            await websocket.send_json(update)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        ws_connections.discard(websocket)
        logger.info(f"WebSocket disconnected ({len(ws_connections)} clients)")
    except Exception as e:
        ws_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
