# Trade Bot — Project Plan

## Vision
A fully autonomous, multi-platform trading bot that executes strategies across crypto exchanges (CEX/DEX), prediction markets (Polymarket), and perpetual futures (Hyperliquid/dYdX). Modular strategy system with backtesting, paper trading, and a web dashboard.

## Tech Stack
- **Core Engine**: Python 3.11+
- **Backtesting**: vectorbt or custom engine (pandas-based)
- **Exchange Connectivity**: ccxt (CEXs), py_clob_client (Polymarket), web3.py (DEXs), hyperliquid-python-sdk
- **Database**: SQLite initially → PostgreSQL later
- **Dashboard Frontend**: TypeScript + React + Recharts
- **Dashboard Backend**: FastAPI (Python)
- **Alerts**: Telegram bot (optional, later)

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Web Dashboard                   │
│              (React + TypeScript)                 │
└──────────────────────┬──────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────┴──────────────────────────┐
│                 FastAPI Backend                   │
│         (Dashboard API + WebSocket feed)          │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│               Trading Engine (Core)              │
│                                                   │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ Strategy   │  │ Risk      │  │ Position     │ │
│  │ Manager    │  │ Manager   │  │ Manager      │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘ │
│        │              │               │          │
│  ┌─────┴──────────────┴───────────────┴───────┐  │
│  │           Order Execution Engine            │  │
│  └─────────────────────┬──────────────────────┘  │
└────────────────────────┼────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───┴───┐  ┌────────────┴──┐  ┌──────────────┴──┐
│ CEX   │  │ DEX Connector │  │  Polymarket /   │
│(ccxt) │  │ (web3.py)     │  │  Hyperliquid    │
└───────┘  └───────────────┘  └─────────────────┘
```

## Phases

### Phase 1 — Data Layer & Exchange Connectivity (Weeks 1–3)
- [ ] Project scaffolding (folder structure, virtual env, dependencies)
- [ ] CEX connector using ccxt (Binance) — fetch OHLCV, order book, ticker
- [ ] Polymarket connector — fetch markets, odds, CLOB data via WebSocket
- [ ] Hyperliquid connector — fetch perp markets, funding rates
- [ ] Data storage — SQLite schema for candles, trades, market snapshots
- [ ] Data pipeline — scheduled fetching + storage of historical data

### Phase 2 — Backtesting Engine (Weeks 3–6)
- [ ] Backtesting framework with strategy interface (abstract base class)
- [ ] Simulated order execution (market/limit orders, slippage model)
- [ ] Performance metrics: P&L, win rate, max drawdown, Sharpe, Sortino
- [ ] Strategy #1: SMA crossover (baseline)
- [ ] Strategy #2: RSI mean reversion
- [ ] Strategy #3: Bollinger Band breakout
- [ ] Visualization: equity curves, trade markers on charts

### Phase 3 — Paper Trading (Weeks 6–10)
- [ ] Paper trading engine (simulated fills against real-time data)
- [ ] Live data feed integration (WebSocket streams)
- [ ] Strategy runner — execute strategies in real-time, paper mode
- [ ] Logging & trade journal (every trade recorded with reasoning)
- [ ] Comparison: backtest results vs paper results

### Phase 4 — Strategy Expansion (Weeks 10–14)
- [ ] Arbitrage: cross-exchange price monitoring + execution logic
- [ ] Polymarket-specific: odds shift detection, event-driven entries
- [ ] Sentiment analysis: social signals (Twitter/X, news) → trade signals
- [ ] Funding rate arbitrage (Hyperliquid perps vs spot)
- [ ] Strategy combinator: ensemble/vote across multiple strategies

### Phase 5 — Risk Management (Integrated throughout, formalized here)
- [ ] Position sizing (Kelly criterion / fixed fractional)
- [ ] Stop-loss / take-profit automation
- [ ] Max drawdown circuit breaker (pause trading if drawdown > threshold)
- [ ] Correlation monitoring (avoid concentrated risk)
- [ ] Daily/weekly P&L limits

### Phase 6 — Web Dashboard (Weeks 14–18)
- [ ] FastAPI backend: portfolio state, trade history, strategy metrics
- [ ] React frontend: real-time P&L chart, open positions, strategy cards
- [ ] Strategy controls: enable/disable, adjust parameters
- [ ] Backtest runner from UI
- [ ] Alerts configuration

### Phase 7 — Live Trading (When Ready)
- [ ] Switch from paper to live execution
- [ ] Wallet/key management (encrypted storage, never in code)
- [ ] Start with smallest possible position sizes
- [ ] Gradual scale-up based on performance

## Key Principles
1. **Never store private keys in code** — use encrypted env vars or a vault
2. **Every strategy must be backtested AND paper traded** before going live
3. **Risk management is not optional** — it's built into the engine core
4. **Modular design** — every strategy is a plugin, every exchange is a connector
5. **Log everything** — every decision, every trade, every signal

## Folder Structure (Planned)
```
trade-bot/
├── src/
│   ├── connectors/         # Exchange/platform connectors
│   │   ├── binance.py
│   │   ├── polymarket.py
│   │   ├── hyperliquid.py
│   │   └── base.py         # Abstract connector interface
│   ├── strategies/          # Trading strategies (pluggable)
│   │   ├── sma_crossover.py
│   │   ├── rsi_reversion.py
│   │   └── base.py         # Abstract strategy interface
│   ├── engine/              # Core trading engine
│   │   ├── backtester.py
│   │   ├── paper_trader.py
│   │   ├── live_trader.py
│   │   ├── order_manager.py
│   │   └── risk_manager.py
│   ├── data/                # Data fetching & storage
│   │   ├── fetcher.py
│   │   ├── storage.py
│   │   └── models.py
│   ├── api/                 # FastAPI dashboard backend
│   │   └── main.py
│   └── utils/               # Helpers, logging, config
│       ├── config.py
│       └── logger.py
├── dashboard/               # React frontend
├── tests/                   # Test suite
├── data/                    # Local data storage (SQLite, CSVs)
├── config.yaml              # Bot configuration
├── requirements.txt
└── README.md
```
