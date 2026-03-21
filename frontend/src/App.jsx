import { useState } from 'react'
import {
  LayoutDashboard,
  LineChart,
  Bot,
  Settings,
  Bell,
  ChevronDown,
  Wifi,
  WifiOff,
} from 'lucide-react'

import PortfolioOverview from './components/PortfolioOverview'
import EquityChart from './components/EquityChart'
import PositionsTable from './components/PositionsTable'
import OrderBookView from './components/OrderBookView'
import TradeHistory from './components/TradeHistory'
import StrategyPanel from './components/StrategyPanel'
import LiveMarkets from './components/LiveMarkets'

import {
  portfolioStats,
  positions,
  recentTrades,
  orderBook,
  strategies,
  equityCurve,
  liveMarkets,
} from './mockData'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
  { icon: LineChart, label: 'Markets', id: 'markets' },
  { icon: Bot, label: 'Strategies', id: 'strategies' },
  { icon: Settings, label: 'Settings', id: 'settings' },
]

function Sidebar({ active, onNav }) {
  return (
    <aside className="w-16 lg:w-56 h-screen fixed left-0 top-0 flex flex-col border-r border-white/[0.04] bg-dark-800/50 backdrop-blur-xl z-50">
      {/* Logo */}
      <div className="h-16 flex items-center justify-center lg:justify-start lg:px-5 border-b border-white/[0.04]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <span className="hidden lg:block text-sm font-semibold gradient-text">
            TradeBot
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 lg:px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = active === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNav(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                isActive
                  ? 'bg-accent-blue/10 text-accent-blue'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03]'
              }`}
            >
              <item.icon size={18} />
              <span className="hidden lg:block text-sm">{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Connection status */}
      <div className="p-3 lg:px-4 border-t border-white/[0.04]">
        <div className="flex items-center gap-2 text-xs">
          <Wifi size={12} className="text-accent-green" />
          <span className="hidden lg:block text-gray-500">Connected</span>
        </div>
      </div>
    </aside>
  )
}

function Header() {
  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.04] bg-dark-800/30 backdrop-blur-xl sticky top-0 z-40">
      <div>
        <h1 className="text-lg font-semibold text-gray-200">Dashboard</h1>
        <p className="text-xs text-gray-500">
          Paper Trading Mode
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-yellow animate-pulse-glow" />
            Simulated
          </span>
        </p>
      </div>
      <div className="flex items-center gap-3">
        {/* Alerts */}
        <button className="relative p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
          <Bell size={16} className="text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent-red" />
        </button>
        {/* Profile */}
        <button className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-accent-purple to-accent-blue" />
          <span className="text-sm text-gray-300 hidden lg:block">Ashish</span>
          <ChevronDown size={14} className="text-gray-500" />
        </button>
      </div>
    </header>
  )
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Background ambient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent-blue/[0.03] rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-purple/[0.03] rounded-full blur-3xl" />
      </div>

      <Sidebar active={activePage} onNav={setActivePage} />

      <main className="ml-16 lg:ml-56 relative z-10">
        <Header />

        <div className="p-6 space-y-6">
          {/* Row 1: Portfolio stats */}
          <PortfolioOverview stats={portfolioStats} />

          {/* Row 2: Equity chart + Live markets */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <EquityChart data={equityCurve} />
            </div>
            <div>
              <LiveMarkets markets={liveMarkets} />
            </div>
          </div>

          {/* Row 3: Positions */}
          <PositionsTable positions={positions} />

          {/* Row 4: Order Book + Trade History + Strategies */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <OrderBookView orderBook={orderBook} />
            <TradeHistory trades={recentTrades} />
            <StrategyPanel strategies={strategies} />
          </div>
        </div>
      </main>
    </div>
  )
}
