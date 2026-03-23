"""
Strategy Manager — orchestrates strategy evaluation and auto-execution.

Responsibilities:
- Registers and manages multiple strategies
- Runs strategies on a configurable interval
- Converts signals into paper orders (auto-execution)
- Tracks signal history and strategy performance
- Provides API-friendly state for the dashboard
"""

import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

from backend.strategies.base import BaseStrategy, Signal, StrategyConfig
from backend.strategies.sma_crossover import SMACrossoverStrategy
from backend.strategies.rsi_reversion import RSIMeanReversionStrategy
from backend.data.openbb_provider import OpenBBDataProvider
from backend.engine.paper_trader import PaperTradingEngine


# Registry of all available strategy classes
STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "sma_crossover": SMACrossoverStrategy,
    "rsi_reversion": RSIMeanReversionStrategy,
}


class StrategyManager:
    """
    Manages strategy lifecycle: register, evaluate, execute.

    Usage:
        manager = StrategyManager(data_provider, paper_engine)
        manager.register_strategy("sma_crossover")
        manager.start()  # Begins auto-evaluation loop
    """

    def __init__(
        self,
        data_provider: OpenBBDataProvider,
        paper_engine: PaperTradingEngine,
        eval_interval: float = 60.0,  # Evaluate strategies every 60 seconds
    ):
        self.data = data_provider
        self.engine = paper_engine
        self.eval_interval = eval_interval

        self._strategies: dict[str, BaseStrategy] = {}
        self._signals: list[dict] = []  # All signals (for the activity feed)
        self._executions: list[dict] = []  # Auto-executed trades from signals
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {
            "total_signals": 0,
            "total_executions": 0,
            "last_eval_at": None,
        }

    # ─── Strategy Registration ────────────────────────────────

    def register_strategy(
        self, strategy_key: str, config: Optional[StrategyConfig] = None
    ) -> dict:
        """
        Register a strategy by its registry key.

        Returns:
            Strategy info dict, or error dict.
        """
        cls = STRATEGY_REGISTRY.get(strategy_key)
        if not cls:
            return {"error": f"Unknown strategy: {strategy_key}. Available: {list(STRATEGY_REGISTRY.keys())}"}

        strategy = cls(config)
        self._strategies[strategy.name] = strategy
        logger.info(f"Registered strategy: {strategy.name} (enabled={strategy.config.enabled})")
        return strategy.to_dict()

    def unregister_strategy(self, name: str) -> dict:
        if name in self._strategies:
            del self._strategies[name]
            return {"success": True}
        return {"error": f"Strategy '{name}' not found"}

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        return self._strategies.get(name)

    def list_strategies(self) -> list[dict]:
        result = []
        for s in self._strategies.values():
            d = s.to_dict()
            # Add execution stats
            exec_count = sum(1 for e in self._executions if e["strategy"] == s.name)
            d["executionCount"] = exec_count
            result.append(d)
        return result

    def list_available(self) -> list[dict]:
        """List all available strategy types (registered or not)."""
        result = []
        for key, cls in STRATEGY_REGISTRY.items():
            instance = cls()
            result.append({
                "key": key,
                "name": instance.name,
                "description": instance.description,
                "configurableParams": instance.configurable_params,
                "defaultConfig": {
                    "params": instance.config.params,
                    "markets": instance.config.markets,
                    "maxPositionSize": instance.config.max_position_size,
                },
                "registered": instance.name in self._strategies,
            })
        return result

    # ─── Strategy Configuration ───────────────────────────────

    def update_strategy_config(self, name: str, updates: dict) -> dict:
        """Update a registered strategy's configuration."""
        strategy = self._strategies.get(name)
        if not strategy:
            return {"error": f"Strategy '{name}' not found"}

        if "enabled" in updates:
            strategy.config.enabled = updates["enabled"]
        if "markets" in updates:
            strategy.config.markets = updates["markets"]
        if "maxPositionSize" in updates:
            strategy.config.max_position_size = updates["maxPositionSize"]
        if "params" in updates:
            strategy.config.params.update(updates["params"])

        logger.info(f"Updated strategy config: {name}")
        return strategy.to_dict()

    # ─── Evaluation Loop ──────────────────────────────────────

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._eval_loop())
            logger.info(f"Strategy manager started (eval every {self.eval_interval}s)")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _eval_loop(self):
        """Periodically evaluate all enabled strategies."""
        # Wait for data provider to have data
        for _ in range(30):
            if self.data.is_running():
                break
            await asyncio.sleep(2)

        while self._running:
            try:
                await self._evaluate_all()
            except Exception as e:
                logger.error(f"Strategy evaluation error: {e}")
            await asyncio.sleep(self.eval_interval)

    async def _evaluate_all(self):
        """Run all enabled strategies against their configured markets."""
        self._stats["last_eval_at"] = datetime.utcnow().isoformat()

        for strategy in self._strategies.values():
            if not strategy.config.enabled:
                continue

            for market_id in strategy.config.markets:
                try:
                    df = self.data.get_historical_df(market_id)
                    indicators = self.data.get_indicators(market_id)
                    current_price = self.data.get_price(market_id, "buy")

                    if not df is not None and current_price <= 0:
                        continue

                    # Check if we have an existing position
                    position = self.engine.positions.get(market_id)
                    has_position = position is not None
                    position_side = position.side if position else None

                    signal = strategy.evaluate(
                        market_id=market_id,
                        df=df,
                        indicators=indicators,
                        current_price=current_price,
                        has_position=has_position,
                        position_side=position_side,
                    )

                    if signal:
                        self._stats["total_signals"] += 1
                        signal_dict = signal.to_dict()
                        signal_dict["executed"] = False
                        self._signals.append(signal_dict)

                        # Auto-execute
                        await self._execute_signal(signal)

                except Exception as e:
                    logger.error(f"Error evaluating {strategy.name} on {market_id}: {e}")

        # Trim signal history
        if len(self._signals) > 200:
            self._signals = self._signals[-200:]
        if len(self._executions) > 200:
            self._executions = self._executions[-200:]

    async def _execute_signal(self, signal: Signal):
        """Convert a signal into a paper order."""
        if signal.suggested_size <= 0:
            return

        current_price = self.data.get_price(signal.market_id, signal.side)
        if current_price <= 0:
            return

        # Calculate shares from dollar amount
        size_dollars = signal.suggested_size
        size_shares = size_dollars / current_price

        if size_shares < 0.0001:
            return

        # Place the order via paper engine
        result = self.engine.place_order(
            market_id=signal.market_id,
            side=signal.side,
            order_type="market",
            size=round(size_shares, 6),
            price=current_price,
        )

        if "error" in result:
            logger.warning(f"Strategy auto-trade failed: {result['error']}")
            return

        self._stats["total_executions"] += 1

        execution = {
            "strategy": signal.strategy,
            "signal": signal.to_dict(),
            "order": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._executions.append(execution)

        # Mark signal as executed
        if self._signals:
            self._signals[-1]["executed"] = True

        logger.info(
            f"Auto-executed: {signal.strategy} → {signal.side.upper()} "
            f"{size_shares:.4f} shares of {signal.market_name} @ ${current_price:.2f} "
            f"(${size_dollars:.2f})"
        )

    # ─── Trigger manual evaluation ────────────────────────────

    async def evaluate_now(self) -> list[dict]:
        """Force an immediate evaluation of all strategies. Returns new signals."""
        before = len(self._signals)
        await self._evaluate_all()
        new_signals = self._signals[before:]
        return new_signals

    # ─── State for API ────────────────────────────────────────

    def get_signals(self, limit: int = 50) -> list[dict]:
        return self._signals[-limit:]

    def get_executions(self, limit: int = 50) -> list[dict]:
        return self._executions[-limit:]

    def get_stats(self) -> dict:
        return {
            **self._stats,
            "active_strategies": sum(1 for s in self._strategies.values() if s.config.enabled),
            "total_strategies": len(self._strategies),
        }
