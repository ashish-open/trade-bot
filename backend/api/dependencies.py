"""
Shared dependencies for API routes.

Holds the global connector instances that routes access.
This avoids circular imports and gives every route file
a clean way to get the current connector state.
"""

from typing import Optional
from backend.connectors.polymarket import PolymarketConnector

# Global connector — initialized in main.py on startup
_polymarket: Optional[PolymarketConnector] = None


def get_polymarket() -> Optional[PolymarketConnector]:
    """Get the global Polymarket connector instance."""
    return _polymarket


def set_polymarket(connector: PolymarketConnector) -> None:
    """Set the global Polymarket connector (called on startup)."""
    global _polymarket
    _polymarket = connector
