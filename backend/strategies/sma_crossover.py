"""
SMA Crossover Strategy — trend-following using Simple Moving Averages.

Signal logic:
- BUY when fast SMA crosses above slow SMA (golden cross)
- SELL when fast SMA crosses below slow SMA (death cross)
- Signal strength scales with the gap between the two SMAs

Configurable parameters:
- fast_period: Fast SMA period (default: 10)
- slow_period: Slow SMA period (default: 20)
- threshold: Minimum % gap between SMAs to trigger (default: 0.5%)
"""

from typing import Optional
import pandas as pd

from backend.strategies.base import BaseStrategy, Signal, StrategyConfig


class SMACrossoverStrategy(BaseStrategy):

    @property
    def name(self) -> str:
        return "SMA Crossover"

    @property
    def description(self) -> str:
        fast = self.config.get("fast_period", 10)
        slow = self.config.get("slow_period", 20)
        return f"Trend-following: buys on golden cross (SMA{fast} > SMA{slow}), sells on death cross"

    def default_config(self) -> StrategyConfig:
        return StrategyConfig(
            params={
                "fast_period": 10,
                "slow_period": 20,
                "threshold": 0.005,  # 0.5% minimum gap
            },
            markets=["bin-btc-usdt", "bin-eth-usdt", "bin-sol-usdt"],
            max_position_size=500.0,
            order_type="market",
            enabled=True,
        )

    @property
    def configurable_params(self) -> list[dict]:
        return [
            {
                "name": "fast_period",
                "type": "int",
                "default": 10,
                "description": "Fast SMA period (days)",
                "min": 3,
                "max": 50,
            },
            {
                "name": "slow_period",
                "type": "int",
                "default": 20,
                "description": "Slow SMA period (days)",
                "min": 10,
                "max": 200,
            },
            {
                "name": "threshold",
                "type": "float",
                "default": 0.005,
                "description": "Minimum SMA gap to trigger signal (as fraction, e.g. 0.005 = 0.5%)",
                "min": 0.001,
                "max": 0.05,
            },
        ]

    def evaluate(
        self,
        market_id: str,
        df: pd.DataFrame,
        indicators: dict,
        current_price: float,
        has_position: bool,
        position_side: Optional[str] = None,
    ) -> Optional[Signal]:
        fast_period = int(self.config.get("fast_period", 10))
        slow_period = int(self.config.get("slow_period", 20))
        threshold = float(self.config.get("threshold", 0.005))

        if df is None or len(df) < slow_period + 2:
            return None

        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]

        # Calculate SMAs
        fast_sma = close.rolling(fast_period).mean()
        slow_sma = close.rolling(slow_period).mean()

        if fast_sma.iloc[-1] != fast_sma.iloc[-1] or slow_sma.iloc[-1] != slow_sma.iloc[-1]:
            return None  # NaN check

        current_fast = float(fast_sma.iloc[-1])
        current_slow = float(slow_sma.iloc[-1])
        prev_fast = float(fast_sma.iloc[-2])
        prev_slow = float(slow_sma.iloc[-2])

        gap = (current_fast - current_slow) / current_slow if current_slow > 0 else 0
        prev_gap = (prev_fast - prev_slow) / prev_slow if prev_slow > 0 else 0

        meta = self._get_market_meta(market_id)

        # Golden cross: fast crosses above slow
        if prev_gap <= 0 and gap > threshold and not has_position:
            strength = min(1.0, abs(gap) / (threshold * 5))
            signal = Signal(
                market_id=market_id,
                market_name=meta["name"],
                side="buy",
                strength=strength,
                reason=f"Golden cross: SMA{fast_period} ({current_fast:.2f}) crossed above SMA{slow_period} ({current_slow:.2f}), gap {gap*100:.2f}%",
                strategy=self.name,
                suggested_size=self.config.max_position_size * strength,
            )
            self.record_signal(signal)
            return signal

        # Death cross: fast crosses below slow — sell if we have a position
        if prev_gap >= 0 and gap < -threshold and has_position:
            strength = min(1.0, abs(gap) / (threshold * 5))
            signal = Signal(
                market_id=market_id,
                market_name=meta["name"],
                side="sell",
                strength=strength,
                reason=f"Death cross: SMA{fast_period} ({current_fast:.2f}) crossed below SMA{slow_period} ({current_slow:.2f}), gap {gap*100:.2f}%",
                strategy=self.name,
                suggested_size=self.config.max_position_size,  # Sell entire position
            )
            self.record_signal(signal)
            return signal

        return None

    def _get_market_meta(self, market_id: str) -> dict:
        from backend.data.openbb_provider import CRYPTO_SYMBOLS
        meta = CRYPTO_SYMBOLS.get(market_id, {})
        return {"name": meta.get("name", market_id), "symbol": meta.get("symbol", "")}
