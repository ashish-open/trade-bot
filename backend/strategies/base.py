"""
Base Strategy — pluggable architecture for building custom trading strategies.

Every strategy inherits from BaseStrategy and implements:
- evaluate(market_id, df, indicators) -> Signal or None
- name, description, default_config

Strategies are pure signal generators. The StrategyManager handles execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

import pandas as pd


@dataclass
class StrategyConfig:
    """
    User-configurable parameters for a strategy instance.

    Every strategy has a default config, and users can customize
    parameters via the API/frontend.
    """
    params: dict[str, Any] = field(default_factory=dict)
    markets: list[str] = field(default_factory=list)  # Market IDs to trade
    max_position_size: float = 500.0  # Max $ per position
    order_type: str = "market"  # "market" or "limit"
    enabled: bool = True

    def get(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)


@dataclass
class Signal:
    """
    A trading signal produced by a strategy.

    The StrategyManager converts signals into paper orders.
    """
    market_id: str
    market_name: str
    side: str            # "buy" or "sell"
    strength: float      # 0.0 to 1.0 (confidence)
    reason: str          # Human-readable reason
    strategy: str        # Name of the strategy that generated it
    suggested_size: float = 0.0  # Suggested position size in $
    suggested_price: float = 0.0  # For limit orders
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "marketId": self.market_id,
            "market": self.market_name,
            "side": self.side,
            "strength": round(self.strength, 2),
            "reason": self.reason,
            "strategy": self.strategy,
            "suggestedSize": round(self.suggested_size, 2),
            "suggestedPrice": round(self.suggested_price, 2),
            "timestamp": self.timestamp,
        }


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Subclass this and implement `evaluate()` to create a new strategy.
    Register it with the StrategyManager to activate it.
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or self.default_config()
        self._signals_history: list[Signal] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this strategy."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        ...

    @abstractmethod
    def default_config(self) -> StrategyConfig:
        """Return the default configuration for this strategy."""
        ...

    @abstractmethod
    def evaluate(
        self,
        market_id: str,
        df: pd.DataFrame,
        indicators: dict,
        current_price: float,
        has_position: bool,
        position_side: Optional[str] = None,
    ) -> Optional[Signal]:
        """
        Evaluate market data and return a Signal (or None if no action).

        Args:
            market_id: The market identifier
            df: Historical OHLCV DataFrame
            indicators: Pre-computed technical indicators dict
            current_price: Latest price
            has_position: Whether we currently have a position in this market
            position_side: "buy"/"sell" side of existing position, if any

        Returns:
            Signal if the strategy wants to trade, None otherwise
        """
        ...

    @property
    def configurable_params(self) -> list[dict]:
        """
        Return list of parameters the user can configure.
        Override in subclass to define custom parameters.

        Returns:
            List of dicts with keys: name, type, default, description, min, max
        """
        return []

    def record_signal(self, signal: Signal):
        """Record a signal in history."""
        self._signals_history.append(signal)
        # Keep last 100 signals
        if len(self._signals_history) > 100:
            self._signals_history = self._signals_history[-100:]

    def get_signal_history(self) -> list[dict]:
        return [s.to_dict() for s in self._signals_history]

    def to_dict(self) -> dict:
        """Serialize strategy state for the API."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.config.enabled,
            "markets": self.config.markets,
            "maxPositionSize": self.config.max_position_size,
            "params": self.config.params,
            "configurableParams": self.configurable_params,
            "recentSignals": [s.to_dict() for s in self._signals_history[-5:]],
        }
