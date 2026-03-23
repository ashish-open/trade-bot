"""
Shared dependencies for API routes.

Holds the global engine instances that routes access.
This avoids circular imports and gives every route file
a clean way to get the current state.
"""

from typing import Optional
from backend.engine.paper_trader import PaperTradingEngine
from backend.connectors.polymarket_feed import PolymarketFeed
from backend.data.openbb_provider import OpenBBDataProvider
from backend.strategies.manager import StrategyManager

# Global instances — initialized in main.py on startup
_paper_engine: Optional[PaperTradingEngine] = None
_polymarket_feed: Optional[PolymarketFeed] = None
_data_provider: Optional[OpenBBDataProvider] = None
_strategy_manager: Optional[StrategyManager] = None


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

def get_data_provider() -> Optional[OpenBBDataProvider]:
    return _data_provider

def set_data_provider(provider: OpenBBDataProvider) -> None:
    global _data_provider
    _data_provider = provider

def get_strategy_manager() -> Optional[StrategyManager]:
    return _strategy_manager

def set_strategy_manager(manager: StrategyManager) -> None:
    global _strategy_manager
    _strategy_manager = manager


# Provider instances for equity, forex, and macro data
_equity_provider = None
_forex_provider = None
_macro_provider = None


def get_equity_provider():
    return _equity_provider

def set_equity_provider(p):
    global _equity_provider
    _equity_provider = p


def get_forex_provider():
    return _forex_provider

def set_forex_provider(p):
    global _forex_provider
    _forex_provider = p


def get_macro_provider():
    return _macro_provider

def set_macro_provider(p):
    global _macro_provider
    _macro_provider = p
