import { useState, useEffect, useCallback } from 'react'
import {
  LayoutDashboard,
  LineChart,
  Settings,
  Wifi,
  WifiOff,
  DollarSign,
  Bot,
  Target,
  Coins,
  Zap,
  Globe,
  Terminal,
  TrendingUp,
  BarChart3,
  Landmark,
  X,
} from 'lucide-react'

import PortfolioOverview from './components/PortfolioOverview'
import PositionsTable from './components/PositionsTable'
import OrderBookView from './components/OrderBookView'
import TradeHistory from './components/TradeHistory'
import LiveMarkets from './components/LiveMarkets'
import TradePanel from './components/TradePanel'
import OpenOrders from './components/OpenOrders'
import MarketsPage from './components/MarketsPage'
import SettingsPage from './components/SettingsPage'
import TerminalPanel from './components/TerminalPanel'
import StrategyPanel from './components/StrategyPanel'
import MarketTickerBar from './components/MarketTickerBar'
import EquityPage from './components/EquityPage'
import ForexPage from './components/ForexPage'
import MacroPage from './components/MacroPage'
import useWebSocket from './useWebSocket'
import * as api from './api'

const PLATFORM_ICONS = { polymarket: Target, binance: Coins, hyperliquid: Zap }

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
  { icon: LineChart, label: 'Crypto', id: 'markets' },
  { icon: TrendingUp, label: 'Stocks', id: 'equity' },
  { icon: DollarSign, label: 'Forex', id: 'forex' },
  { icon: Landmark, label: 'Economy', id: 'macro' },
  { icon: Settings, label: 'Settings', id: 'settings' },
]

function Sidebar({ active, onNav, connected, onOpenTerminal }) {
  return (
    <aside className="w-16 lg:w-56 h-screen fixed left-0 top-0 flex flex-col border-r border-white/[0.04] bg-dark-800/50 backdrop-blur-xl z-50">
      <div className="h-16 flex items-center justify-center lg:justify-start lg:px-5 border-b border-white/[0.04]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <span className="hidden lg:block text-sm font-semibold gradient-text">TradeBot Elite</span>
        </div>
      </div>
      <nav className="flex-1 py-4 px-2 lg:px-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNav(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
              active === item.id
                ? 'bg-accent-blue/10 text-accent-blue'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03]'
            }`}
          >
            <item.icon size={18} />
            <span className="hidden lg:block text-sm">{item.label}</span>
          </button>
        ))}

        {/* Terminal button */}
        <button
          onClick={onOpenTerminal}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-accent-cyan hover:bg-accent-cyan/[0.06] border border-accent-cyan/20 mt-4"
        >
          <Terminal size={18} />
          <span className="hidden lg:block text-sm font-medium">Terminal</span>
        </button>
      </nav>
      <div className="p-3 lg:px-4 border-t border-white/[0.04]">
        <div className="flex items-center gap-2 text-xs">
          {connected ? (
            <>
              <Wifi size={12} className="text-accent-green" />
              <span className="hidden lg:block text-gray-500">Live Data</span>
            </>
          ) : (
            <>
              <WifiOff size={12} className="text-accent-red" />
              <span className="hidden lg:block text-gray-500">Disconnected</span>
            </>
          )}
        </div>
      </div>
    </aside>
  )
}

function Header({ cash, activePlatform, platforms, onPlatformChange, activePage }) {
  const pageLabels = {
    dashboard: 'Dashboard',
    markets: 'Crypto Markets',
    equity: 'Stocks & ETFs',
    forex: 'Forex',
    macro: 'Economy',
    settings: 'Settings',
  }

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.04] bg-dark-800/30 backdrop-blur-xl sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-200">{pageLabels[activePage] || 'Dashboard'}</h1>
          <p className="text-xs text-gray-500">
            Paper Trading Mode
            {platforms.some((p) => p.dataSource === 'live') ? (
              <span className="ml-2 inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-glow" />
                Live Data
              </span>
            ) : (
              <span className="ml-2 inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-yellow animate-pulse-glow" />
                Connecting...
              </span>
            )}
          </p>
        </div>

        {/* Platform pills — only show on dashboard/markets */}
        {(activePage === 'dashboard' || activePage === 'markets') && (
          <div className="hidden md:flex items-center gap-1 ml-4 px-1 py-1 rounded-xl bg-white/[0.03]">
            <button
              onClick={() => onPlatformChange('')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activePlatform === ''
                  ? 'bg-accent-blue/20 text-accent-blue'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <Globe size={12} />
              All
            </button>
            {platforms.map((p) => {
              const Icon = PLATFORM_ICONS[p.id] || Globe
              return (
                <button
                  key={p.id}
                  onClick={() => onPlatformChange(p.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activePlatform === p.id
                      ? 'bg-accent-blue/20 text-accent-blue'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  <Icon size={12} />
                  {p.label}
                  <span className="text-gray-600 tabular-nums">{p.marketCount}</span>
                  {p.dataSource === 'live' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-glow" title="Live data" />
                  )}
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/[0.03] text-sm">
          <DollarSign size={14} className="text-accent-green" />
          <span className="text-gray-400">Cash:</span>
          <span className="text-gray-200 tabular-nums font-medium">
            ${(cash || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <button className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-accent-purple to-accent-blue" />
          <span className="text-sm text-gray-300 hidden lg:block">Rythwik</span>
        </button>
      </div>
    </header>
  )
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [activePlatform, setActivePlatform] = useState('')
  const [platforms, setPlatforms] = useState([])
  const [portfolio, setPortfolio] = useState({
    totalValue: 10000, cash: 10000, totalPnl: 0, totalPnlPercent: 0,
    dayPnl: 0, dayPnlPercent: 0, winRate: 0, totalTrades: 0,
    openPositions: 0, activeStrategies: 0,
  })
  const [positions, setPositions] = useState([])
  const [markets, setMarkets] = useState([])
  const [allMarkets, setAllMarkets] = useState([])
  const [trades, setTrades] = useState([])
  const [openOrders, setOpenOrders] = useState([])
  const [selectedMarket, setSelectedMarket] = useState(null)
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
  const [notification, setNotification] = useState(null)
  const [terminalOpen, setTerminalOpen] = useState(false)
  const [strategies, setStrategies] = useState([])
  const [strategyStats, setStrategyStats] = useState(null)
  const [macroData, setMacroData] = useState(null)

  const { data: wsData, connected } = useWebSocket()

  // ── Process WebSocket ticks ─────────────────────────────────
  useEffect(() => {
    if (!wsData) return
    if (wsData.portfolio) {
      setPortfolio((prev) => ({ ...prev, ...wsData.portfolio }))
    }
    if (wsData.positions) {
      setPositions(wsData.positions)
    }
    if (wsData.markets) {
      setAllMarkets((prev) => {
        const priceMap = {}
        wsData.markets.forEach((m) => { priceMap[m.id] = m })
        const existingIds = new Set(prev.map(m => m.id))
        const newMarkets = wsData.markets
          .filter(m => !existingIds.has(m.id))
          .map(m => ({ ...m, name: m.id, symbol: m.id }))
        return [
          ...prev.map((m) => {
            const update = priceMap[m.id]
            return update ? { ...m, price: update.price, change: update.change, dataSource: update.dataSource || m.dataSource } : m
          }),
          ...newMarkets,
        ]
      })
    }
    if (wsData.strategies) {
      setStrategyStats(wsData.strategies)
      setPortfolio(prev => ({ ...prev, activeStrategies: wsData.strategies.activeStrategies || 0 }))
    }
    if (wsData.macro) {
      setMacroData(wsData.macro)
    }
  }, [wsData])

  // ── Initial data load ───────────────────────────────────────
  useEffect(() => {
    async function load() {
      try {
        const [plats, mkts, port, trds, ords, strats] = await Promise.all([
          api.getPlatforms(),
          api.getMarkets('', '', 100),
          api.getPortfolio(),
          api.getTradeHistory(),
          api.getOpenOrders(),
          api.getStrategies().catch(() => []),
        ])
        setPlatforms(plats)
        setAllMarkets(mkts)
        setPortfolio(port)
        setTrades(trds)
        setOpenOrders(ords)
        setStrategies(strats)
        if (mkts.length > 0 && !selectedMarket) setSelectedMarket(mkts[0])
      } catch (e) {
        console.error('Failed to load initial data:', e)
      }

      // Load macro data separately (non-blocking)
      try {
        const macro = await api.getMacroOverview()
        setMacroData(macro)
      } catch (e) {
        console.error('Failed to load macro data:', e)
      }
    }
    load()
  }, [])

  // ── Filter markets when platform changes ──────────────────
  useEffect(() => {
    if (activePlatform) {
      setMarkets(allMarkets.filter((m) => m.platform === activePlatform))
    } else {
      setMarkets(allMarkets)
    }
  }, [activePlatform, allMarkets])

  // ── Order book polling ──────────────────────────────────────
  useEffect(() => {
    if (!selectedMarket) return
    api.getOrderbook(selectedMarket.id).then(setOrderBook).catch(console.error)
    const interval = setInterval(() => {
      api.getOrderbook(selectedMarket.id).then(setOrderBook).catch(() => {})
    }, 2000)
    return () => clearInterval(interval)
  }, [selectedMarket?.id])

  // ── Refresh trades + orders + strategies periodically ──────
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [trds, ords, strats] = await Promise.all([
          api.getTradeHistory(),
          api.getOpenOrders(),
          api.getStrategies().catch(() => []),
        ])
        setTrades(trds)
        setOpenOrders(ords)
        if (strats && strats.length) setStrategies(strats)
      } catch {}
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // ── Actions ─────────────────────────────────────────────────

  const notify = (type, message) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 4000)
  }

  const handlePlaceOrder = useCallback(async (orderData) => {
    try {
      const result = await api.placeOrder(orderData)
      if (result.error) {
        notify('error', result.error)
      } else {
        notify('success', `${result.side.toUpperCase()} ${result.size} shares of ${result.market || selectedMarket?.name} @ $${result.price.toFixed(4)}`)
        const [port, trds, ords] = await Promise.all([
          api.getPortfolio(), api.getTradeHistory(), api.getOpenOrders(),
        ])
        setPortfolio(port)
        setPositions(port.positions || [])
        setTrades(trds)
        setOpenOrders(ords)
      }
    } catch (e) {
      notify('error', e.message)
    }
  }, [selectedMarket])

  const handleCancelOrder = useCallback(async (orderId) => {
    try {
      await api.cancelOrder(orderId)
      notify('success', 'Order cancelled')
      setOpenOrders((prev) => prev.filter((o) => o.id !== orderId))
    } catch (e) {
      notify('error', e.message)
    }
  }, [])

  const handleClosePosition = useCallback(async (pos) => {
    try {
      const result = await api.placeOrder({
        market_id: pos.id,
        side: 'sell',
        order_type: 'market',
        size: pos.size,
      })
      if (result.error) {
        notify('error', result.error)
      } else {
        notify('success', `Closed ${pos.size} shares of ${pos.market} — P&L: ${pos.pnl >= 0 ? '+' : ''}$${pos.pnl.toFixed(2)}`)
        const [port, trds] = await Promise.all([
          api.getPortfolio(), api.getTradeHistory(),
        ])
        setPortfolio(port)
        setPositions(port.positions || [])
        setTrades(trds)
      }
    } catch (e) {
      notify('error', e.message)
    }
  }, [])

  const handleSelectMarket = useCallback((market) => {
    setSelectedMarket(market)
  }, [])

  const refreshStrategies = useCallback(async () => {
    try {
      const strats = await api.getStrategies()
      setStrategies(strats)
    } catch {}
  }, [])

  // Filter markets for display
  const filteredMarkets = activePlatform
    ? markets.filter((m) => m.platform === activePlatform)
    : markets

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Background ambient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent-blue/[0.03] rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-purple/[0.03] rounded-full blur-3xl" />
      </div>

      {/* Notification toast */}
      {notification && (
        <div className={`fixed top-4 right-4 z-[100] px-4 py-3 rounded-xl text-sm font-medium animate-fade-in ${
          notification.type === 'error'
            ? 'bg-accent-red/20 text-accent-red border border-accent-red/30'
            : 'bg-accent-green/20 text-accent-green border border-accent-green/30'
        }`}>
          {notification.message}
        </div>
      )}

      <Sidebar
        active={activePage}
        onNav={setActivePage}
        connected={connected}
        onOpenTerminal={() => setTerminalOpen(true)}
      />

      <main className="ml-16 lg:ml-56 relative z-10">
        {/* Global Ticker Bar */}
        <MarketTickerBar macro={macroData} />

        <Header
          cash={portfolio.cash}
          activePlatform={activePlatform}
          platforms={platforms}
          onPlatformChange={setActivePlatform}
          activePage={activePage}
        />

        {activePage === 'dashboard' && (
          <div className="p-6 space-y-6">
            {/* Row 1: Portfolio stats */}
            <PortfolioOverview stats={portfolio} />

            {/* Row 2: Trade Panel + Live Markets */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TradePanel
                  market={selectedMarket}
                  onPlaceOrder={handlePlaceOrder}
                  cash={portfolio.cash}
                  positions={positions}
                />
              </div>
              <div>
                <LiveMarkets
                  markets={filteredMarkets}
                  selectedId={selectedMarket?.id}
                  onSelect={handleSelectMarket}
                />
              </div>
            </div>

            {/* Row 2.5: Strategies */}
            <StrategyPanel strategies={strategies} onRefresh={refreshStrategies} />

            {/* Row 3: Positions */}
            {positions.length > 0 && (
              <PositionsTable positions={positions} onClose={handleClosePosition} />
            )}

            {/* Row 4: Open Orders */}
            {openOrders.length > 0 && (
              <OpenOrders orders={openOrders} onCancel={handleCancelOrder} />
            )}

            {/* Row 5: Order Book + Trade History */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <OrderBookView
                orderBook={orderBook}
                marketName={selectedMarket?.name || ''}
              />
              <TradeHistory trades={trades} />
            </div>
          </div>
        )}

        {activePage === 'markets' && (
          <MarketsPage
            markets={filteredMarkets}
            activePlatform={activePlatform}
            platforms={platforms}
            onPlatformChange={setActivePlatform}
            onSelectMarket={(market) => {
              setSelectedMarket(market)
              setActivePage('dashboard')
            }}
          />
        )}

        {activePage === 'equity' && <EquityPage />}
        {activePage === 'forex' && <ForexPage />}
        {activePage === 'macro' && <MacroPage />}

        {activePage === 'settings' && (
          <SettingsPage />
        )}
      </main>

      {/* Bloomberg-style Terminal Panel (slide-out) */}
      <TerminalPanel
        open={terminalOpen}
        onClose={() => setTerminalOpen(false)}
        markets={filteredMarkets}
        allMarkets={allMarkets}
        selectedMarket={selectedMarket}
        onSelectMarket={handleSelectMarket}
        orderBook={orderBook}
        portfolio={portfolio}
        positions={positions}
        trades={trades}
        onPlaceOrder={handlePlaceOrder}
        onClosePosition={handleClosePosition}
      />
    </div>
  )
}
