"""
RSI Mean Reversion Strategy — buy oversold, sell overbought.

Signal logic:
- BUY when RSI drops below oversold threshold (default: 30)
- SELL when RSI rises above overbought threshold (default: 70)
- Signal strength scales with how extreme the RSI reading is

Configurable parameters:
- rsi_period: RSI calculation period (default: 14)
- oversold: RSI level to trigger buy (default: 30)
- overbought: RSI level to trigger sell (default: 70)
"""

from typing import Optional
import pandas as pd
import ta

from backend.strategies.base import BaseStrategy, Signal, StrategyConfig


class RSIMeanReversionStrategy(BaseStrategy):

    @property
    def name(self) -> str:
        return "RSI Mean Reversion"

    @property
    def description(self) -> str:
        ob = self.config.get("overbought", 70)
        os_ = self.config.get("oversold", 30)
        return f"Mean reversion: buys when RSI < {os_} (oversold), sells when RSI > {ob} (overbought)"

    def default_config(self) -> StrategyConfig:
        return StrategyConfig(
            params={
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
            },
            markets=["bin-btc-usdt", "bin-eth-usdt", "bin-sol-usdt"],
            max_position_size=500.0,
            order_type="market",
            enabled=False,  # Disabled by default — user activates it
        )

    @property
    def configurable_params(self) -> list[dict]:
        return [
            {
                "name": "rsi_period",
                "type": "int",
                "default": 14,
                "description": "RSI calculation period (days)",
                "min": 5,
                "max": 50,
            },
            {
                "name": "oversold",
                "type": "float",
                "default": 30,
                "description": "RSI level to trigger buy signal",
                "min": 10,
                "max": 40,
            },
            {
                "name": "overbought",
                "type": "float",
                "default": 70,
                "description": "RSI level to trigger sell signal",
                "min": 60,
                "max": 95,
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
        rsi_period = int(self.config.get("rsi_period", 14))
        oversold = float(self.config.get("oversold", 30))
        overbought = float(self.config.get("overbought", 70))

        if df is None or len(df) < rsi_period + 5:
            return None

        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]

        # Compute RSI
        rsi_indicator = ta.momentum.RSIIndicator(close, window=rsi_period)
        rsi_series = rsi_indicator.rsi()
        current_rsi = float(rsi_series.iloc[-1])
        prev_rsi = float(rsi_series.iloc[-2])

        if current_rsi != current_rsi:  # NaN check
            return None

        meta = self._get_market_meta(market_id)

        # Oversold — buy signal
        if current_rsi < oversold and not has_position:
            # Strength: deeper oversold = stronger signal
            strength = min(1.0, (oversold - current_rsi) / 20)
            signal = Signal(
                market_id=market_id,
                market_name=meta["name"],
                side="buy",
                strength=strength,
                reason=f"RSI oversold at {current_rsi:.1f} (threshold: {oversold}), expecting mean reversion upward",
                strategy=self.name,
                suggested_size=self.config.max_position_size * strength,
            )
            self.record_signal(signal)
            return signal

        # Overbought — sell signal
        if current_rsi > overbought and has_position:
            strength = min(1.0, (current_rsi - overbought) / 20)
            signal = Signal(
                market_id=market_id,
                market_name=meta["name"],
                side="sell",
                strength=strength,
                reason=f"RSI overbought at {current_rsi:.1f} (threshold: {overbought}), expecting mean reversion downward",
                strategy=self.name,
                suggested_size=self.config.max_position_size,
            )
            self.record_signal(signal)
            return signal

        return None

    def _get_market_meta(self, market_id: str) -> dict:
        from backend.data.openbb_provider import CRYPTO_SYMBOLS
        meta = CRYPTO_SYMBOLS.get(market_id, {})
        return {"name": meta.get("name", market_id), "symbol": meta.get("symbol", "")}
