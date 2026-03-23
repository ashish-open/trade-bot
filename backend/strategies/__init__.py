# Trading strategies — pluggable strategy framework
from backend.strategies.base import BaseStrategy, Signal, StrategyConfig
from backend.strategies.sma_crossover import SMACrossoverStrategy
from backend.strategies.rsi_reversion import RSIMeanReversionStrategy

__all__ = [
    "BaseStrategy",
    "Signal",
    "StrategyConfig",
    "SMACrossoverStrategy",
    "RSIMeanReversionStrategy",
]
