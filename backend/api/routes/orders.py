"""Order management — place, cancel, list paper orders."""

from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from backend.api.dependencies import get_paper_engine

router = APIRouter(tags=["orders"])


class PlaceOrderRequest(BaseModel):
    market_id: str
    side: str               # "buy" or "sell"
    order_type: str = "market"  # "market" or "limit"
    size: float
    price: Optional[float] = None


@router.post("/orders")
async def place_order(req: PlaceOrderRequest):
    """Place a paper trade order."""
    engine = get_paper_engine()
    if not engine:
        return {"error": "Paper trading engine not running"}

    result = engine.place_order(
        market_id=req.market_id,
        side=req.side,
        order_type=req.order_type,
        size=req.size,
        price=req.price or 0,
    )
    return result


@router.get("/orders")
async def get_open_orders():
    """Get all open (unfilled) limit orders."""
    engine = get_paper_engine()
    if not engine:
        return []

    engine.check_fills()
    return engine.get_open_orders()


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an open limit order."""
    engine = get_paper_engine()
    if not engine:
        return {"error": "Engine not running"}
    return engine.cancel_order(order_id)
