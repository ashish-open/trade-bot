"""
Demo: Polymarket Connector

This script demonstrates how to use the Polymarket connector to:
1. Connect to Polymarket (works without auth for data)
2. Browse and search markets
3. Check prices and order books
4. Place orders (requires auth — private key in .env)

Run: python demo_polymarket.py

Before running:
1. pip install -r requirements.txt
2. Copy .env.example to .env
3. (Optional) Add your private key to .env for trading features
"""

import asyncio
import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.connectors.polymarket import PolymarketConnector
from src.connectors.base import OrderSide, OrderType


async def demo_market_data():
    """
    Demo 1: Explore markets and prices (NO auth needed).
    This works without any private keys or wallet setup.
    """
    print("\n" + "=" * 60)
    print("  DEMO 1: Market Data (no auth required)")
    print("=" * 60)

    connector = PolymarketConnector()
    connected = await connector.connect()

    if not connected:
        print("Failed to connect to Polymarket!")
        return

    # --- Fetch trending markets ---
    print("\n--- Top 5 Active Markets ---")
    markets = await connector.get_markets(limit=5, active=True)

    for i, market in enumerate(markets, 1):
        print(f"\n{i}. {market.name}")
        print(f"   Volume: ${market.extra.get('volume', 'N/A')}")
        print(f"   Active: {market.active}")

        # Show token IDs (needed for pricing/trading)
        tokens = market.extra.get("tokens", [])
        for token in tokens:
            print(f"   → {token['outcome']}: token_id={token['token_id'][:20]}...")

    # --- Search for specific markets ---
    print("\n\n--- Search: 'bitcoin' ---")
    btc_markets = await connector.search_markets("bitcoin", limit=3)
    for m in btc_markets:
        print(f"  • {m.name}")

    # --- Get price & orderbook for first market's first token ---
    if markets and markets[0].extra.get("tokens"):
        token_id = markets[0].extra["tokens"][0]["token_id"]
        outcome = markets[0].extra["tokens"][0]["outcome"]

        print(f"\n\n--- Prices for: {markets[0].name} ({outcome}) ---")

        buy_price = await connector.get_price(token_id, OrderSide.BUY)
        sell_price = await connector.get_price(token_id, OrderSide.SELL)
        midpoint = await connector.get_midpoint(token_id)

        print(f"  Buy price:  ${buy_price:.4f}")
        print(f"  Sell price: ${sell_price:.4f}")
        print(f"  Midpoint:   ${midpoint:.4f}")
        print(f"  Spread:     ${sell_price - buy_price:.4f}")

        print(f"\n--- Order Book (top 5 levels) ---")
        book = await connector.get_orderbook(token_id)
        print(f"  {'BIDS (buyers)':>30}  |  {'ASKS (sellers)':<30}")
        print(f"  {'Price':>15} {'Size':>14}  |  {'Price':<15} {'Size':<14}")
        print(f"  {'-'*30}  |  {'-'*30}")

        max_levels = min(5, max(len(book.bids), len(book.asks)))
        for i in range(max_levels):
            bid_str = ""
            ask_str = ""
            if i < len(book.bids):
                bid_str = f"${book.bids[i]['price']:.4f}  {book.bids[i]['size']:>10.2f}"
            if i < len(book.asks):
                ask_str = f"${book.asks[i]['price']:.4f}  {book.asks[i]['size']:>10.2f}"
            print(f"  {bid_str:>30}  |  {ask_str:<30}")

    await connector.disconnect()
    print("\n✓ Market data demo complete!")


async def demo_trading():
    """
    Demo 2: Trading features (requires auth).
    Only runs if POLYMARKET_PRIVATE_KEY is set in .env
    """
    print("\n" + "=" * 60)
    print("  DEMO 2: Trading (auth required)")
    print("=" * 60)

    connector = PolymarketConnector()
    connected = await connector.connect()

    if not connected:
        print("Failed to connect!")
        return

    if not connector._authenticated:
        print("\n⚠ Skipping trading demo — no credentials configured.")
        print("  To enable: set POLYMARKET_PRIVATE_KEY in your .env file")
        await connector.disconnect()
        return

    # --- Check positions ---
    print("\n--- Your Current Positions ---")
    positions = await connector.get_positions()
    if positions:
        for pos in positions:
            title = pos.extra.get("title", pos.market_id[:20])
            outcome = pos.extra.get("outcome", "")
            print(f"  • {title} [{outcome}]")
            print(f"    Size: {pos.size:.2f} shares @ ${pos.entry_price:.4f}")
            print(f"    Current: ${pos.current_price:.4f}")
            print(f"    P&L: ${pos.unrealized_pnl:.2f} ({pos.pnl_percent:.1f}%)")
    else:
        print("  No active positions")

    # --- Check open orders ---
    print("\n--- Your Open Orders ---")
    orders = await connector.get_open_orders()
    if orders:
        for o in orders:
            print(f"  • {o.side.value.upper()} {o.size} @ ${o.price:.4f} [{o.status.value}]")
    else:
        print("  No open orders")

    # --- Check balance ---
    print("\n--- Balance ---")
    balance = await connector.get_balance()
    for key, val in balance.items():
        print(f"  {key}: {val}")

    # --- Example: Place a limit order (COMMENTED OUT for safety!) ---
    # Uncomment below to actually place an order:
    #
    # order = await connector.place_order(
    #     market_id="YOUR_TOKEN_ID_HERE",
    #     side=OrderSide.BUY,
    #     order_type=OrderType.GTC,
    #     size=10,        # 10 shares
    #     price=0.30,     # At $0.30 per share
    # )
    # print(f"\nOrder placed! ID: {order.id}")

    # --- Trade history ---
    print("\n--- Recent Trade History (last 5) ---")
    trades = await connector.get_trade_history(limit=5)
    for t in trades:
        print(f"  • {t.get('type', '?')} — {t.get('title', 'Unknown')[:50]}")

    await connector.disconnect()
    print("\n✓ Trading demo complete!")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("  Polymarket Connector Demo")
    print("=" * 60)

    # Demo 1 always runs (no auth needed)
    await demo_market_data()

    # Demo 2 shows trading features (needs auth)
    await demo_trading()

    print("\n" + "=" * 60)
    print("  All demos complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
