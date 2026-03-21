"""Order management endpoints — place, cancel, list orders."""

from typing import Optional
from fastapi import APIRouter, Query

from backend.connectors.base import OrderSide, OrderType
from backend.api.dependencies import get_polymarket

router = APIRouter(tags=["orders"])


@router.post("/orders")
async def place_order(
    token_id: str,
    side: str,
    order_type: str = "gtc",
    size: float = 0,
    price: Optional[float] = None,
):
    """Place an order on Polymarket."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket._authenticated:
        return {"error": "Not authenticated — set credentials in .env"}

    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    otype = OrderType.GTC if order_type.lower() == "gtc" else OrderType.FOK

    try:
        order = await polymarket.place_order(
            market_id=token_id,
            side=order_side,
            order_type=otype,
            size=size,
            price=price,
        )
        return {
            "id": order.id,
            "status": order.status.value,
            "side": order.side.value,
            "price": order.price,
            "size": order.size,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/orders")
async def get_open_orders():
    """Get all open orders."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket._authenticated:
        return []

    orders = await polymarket.get_open_orders()
    return [
        {
            "id": o.id,
            "market": o.market_id[:20],
            "side": o.side.value,
            "price": o.price,
            "size": o.size,
            "status": o.status.value,
        }
        for o in orders
    ]


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an open order."""
    polymarket = get_polymarket()
    if not polymarket or not polymarket._authenticated:
        return {"error": "Not authenticated"}

    success = await polymarket.cancel_order(order_id)
    return {"success": success}
