/**
 * Mock data for the dashboard.
 * This will be replaced with real API calls once the FastAPI backend is wired up.
 * Keeping it separate makes it easy to swap later.
 */

export const portfolioStats = {
  totalValue: 12847.53,
  totalPnl: 1847.53,
  totalPnlPercent: 16.8,
  dayPnl: 234.12,
  dayPnlPercent: 1.85,
  winRate: 68.5,
  totalTrades: 142,
  openPositions: 6,
  activeStrategies: 3,
}

export const positions = [
  {
    id: '1',
    market: 'Will Bitcoin reach $150k by July 2026?',
    platform: 'Polymarket',
    side: 'YES',
    size: 250,
    entryPrice: 0.42,
    currentPrice: 0.58,
    pnl: 40.0,
    pnlPercent: 38.1,
  },
  {
    id: '2',
    market: 'Fed rate cut in June 2026?',
    platform: 'Polymarket',
    side: 'YES',
    size: 500,
    entryPrice: 0.65,
    currentPrice: 0.72,
    pnl: 35.0,
    pnlPercent: 10.77,
  },
  {
    id: '3',
    market: 'ETH/USDT Perp Long',
    platform: 'Hyperliquid',
    side: 'LONG',
    size: 2.5,
    entryPrice: 3820.0,
    currentPrice: 3965.0,
    pnl: 362.5,
    pnlPercent: 3.8,
  },
  {
    id: '4',
    market: 'Will GPT-5 launch before August 2026?',
    platform: 'Polymarket',
    side: 'NO',
    size: 300,
    entryPrice: 0.55,
    currentPrice: 0.48,
    pnl: 21.0,
    pnlPercent: 12.73,
  },
  {
    id: '5',
    market: 'SOL/USDT Spot',
    platform: 'Binance',
    side: 'LONG',
    size: 15,
    entryPrice: 185.0,
    currentPrice: 178.5,
    pnl: -97.5,
    pnlPercent: -3.51,
  },
  {
    id: '6',
    market: 'Will Ethereum ETF see $1B inflows in Q2?',
    platform: 'Polymarket',
    side: 'YES',
    size: 400,
    entryPrice: 0.38,
    currentPrice: 0.41,
    pnl: 12.0,
    pnlPercent: 7.89,
  },
]

export const recentTrades = [
  { id: 1, time: '14:23:05', market: 'BTC $150k by July', side: 'BUY', price: 0.58, size: 50, status: 'filled', pnl: null },
  { id: 2, time: '14:15:32', market: 'Fed rate cut June', side: 'SELL', price: 0.72, size: 100, status: 'filled', pnl: 7.0 },
  { id: 3, time: '13:58:11', market: 'ETH/USDT Perp', side: 'BUY', price: 3965.0, size: 0.5, status: 'filled', pnl: null },
  { id: 4, time: '13:42:28', market: 'GPT-5 before Aug', side: 'SELL', price: 0.52, size: 150, status: 'filled', pnl: -4.5 },
  { id: 5, time: '13:30:00', market: 'SOL/USDT', side: 'BUY', price: 178.5, size: 5, status: 'filled', pnl: null },
  { id: 6, time: '12:55:44', market: 'ETH ETF Inflows', side: 'BUY', price: 0.41, size: 200, status: 'filled', pnl: null },
  { id: 7, time: '12:30:10', market: 'BTC $150k by July', side: 'BUY', price: 0.55, size: 100, status: 'cancelled', pnl: null },
  { id: 8, time: '11:45:22', market: 'Fed rate cut June', side: 'BUY', price: 0.65, size: 200, status: 'filled', pnl: null },
]

export const orderBook = {
  bids: [
    { price: 0.57, size: 1250 },
    { price: 0.56, size: 3400 },
    { price: 0.55, size: 2100 },
    { price: 0.54, size: 5600 },
    { price: 0.53, size: 1800 },
    { price: 0.52, size: 4200 },
    { price: 0.51, size: 2900 },
    { price: 0.50, size: 7500 },
  ],
  asks: [
    { price: 0.58, size: 980 },
    { price: 0.59, size: 2200 },
    { price: 0.60, size: 4100 },
    { price: 0.61, size: 1500 },
    { price: 0.62, size: 3800 },
    { price: 0.63, size: 2600 },
    { price: 0.64, size: 1900 },
    { price: 0.65, size: 5200 },
  ],
}

export const strategies = [
  { id: 1, name: 'SMA Crossover', status: 'active', winRate: 72, trades: 48, pnl: 892.0, platform: 'Binance' },
  { id: 2, name: 'Polymarket Odds Shift', status: 'active', winRate: 65, trades: 35, pnl: 423.5, platform: 'Polymarket' },
  { id: 3, name: 'Funding Rate Arb', status: 'active', winRate: 81, trades: 22, pnl: 532.0, platform: 'Hyperliquid' },
  { id: 4, name: 'RSI Mean Reversion', status: 'paused', winRate: 58, trades: 37, pnl: -67.2, platform: 'Binance' },
]

// Equity curve data (last 30 days)
export const equityCurve = Array.from({ length: 30 }, (_, i) => {
  const base = 11000
  const noise = Math.sin(i * 0.3) * 200 + Math.random() * 150
  const trend = i * 62
  return {
    date: new Date(2026, 1, 19 + i).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: Math.round((base + trend + noise) * 100) / 100,
  }
})

// Live market prices (simulated)
export const liveMarkets = [
  { id: 1, name: 'BTC $150k by July 2026', price: 0.58, change: +0.03, volume: '$1.2M' },
  { id: 2, name: 'Fed rate cut June 2026', price: 0.72, change: +0.01, volume: '$890K' },
  { id: 3, name: 'GPT-5 before Aug 2026', price: 0.48, change: -0.04, volume: '$2.1M' },
  { id: 4, name: 'ETH ETF $1B Q2 inflows', price: 0.41, change: +0.02, volume: '$450K' },
  { id: 5, name: 'Trump wins 2028 primary', price: 0.62, change: +0.05, volume: '$3.8M' },
  { id: 6, name: 'Solana flips Ethereum', price: 0.08, change: -0.01, volume: '$670K' },
]
