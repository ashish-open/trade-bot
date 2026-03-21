"""
Shared dependencies for API routes.

Holds the global engine instances that routes access.
This avoids circular imports and gives every route file
a clean way to get the current state.
"""

from typing import Optional
from backend.engine.market_simulator import MarketSimulator
from backend.engine.paper_trader import PaperTradingEngine
from backend.connectors.polymarket_feed import PolymarketFeed

# Global instances — initialized in main.py on startup
_simulator: Optional[MarketSimulator] = None
_paper_engine: Optional[PaperTradingEngine] = None
_polymarket_feed: Optional[PolymarketFeed] = None


def get_simulator() -> Optional[MarketSimulator]:
    return _simulator

def set_simulator(sim: MarketSimulator) -> None:
    global _simulator
    _simulator = sim

def get_paper_engine() -> Optional[PaperTradingEngine]:
    return _paper_engine

def set_paper_engine(engine: PaperTradingEngine) -> None:
    global _paper_engine
    _paper_engine = engine

def get_polymarket_feed() -> Optional[PolymarketFeed]:
    return _polymarket_feed

def set_polymarket_feed(feed: PolymarketFeed) -> None:
    global _polymarket_feed
    _polymarket_feed = feed
