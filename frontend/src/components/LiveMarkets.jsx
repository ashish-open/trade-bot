import { Search, TrendingUp, TrendingDown, Target, Coins, Zap } from 'lucide-react'
import { useState } from 'react'

const PLATFORM_BADGE = {
  polymarket: { icon: Target, label: 'PM', color: 'text-accent-purple bg-accent-purple/10' },
  binance:    { icon: Coins,  label: 'BN', color: 'text-accent-yellow bg-accent-yellow/10' },
  hyperliquid:{ icon: Zap,    label: 'HL', color: 'text-accent-cyan bg-accent-cyan/10' },
}

export default function LiveMarkets({ markets, selectedId, onSelect }) {
  const [search, setSearch] = useState('')

  const filtered = markets.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    (m.symbol && m.symbol.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Live Markets</h3>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse-glow" />
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-3">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search markets..."
          className="w-full pl-9 pr-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30 transition-colors"
        />
      </div>

      {/* Market list */}
      <div className="space-y-1 max-h-[480px] overflow-y-auto">
        {filtered.map((market) => {
          const isUp = (market.change || 0) >= 0
          const badge = PLATFORM_BADGE[market.platform]
          const decimals = market.marketType === 'prediction' ? 4 : 2
          return (
            <div
              key={market.id}
              onClick={() => onSelect && onSelect(market)}
              className={`flex items-center gap-2 py-2.5 px-2 rounded-lg transition-colors cursor-pointer ${
                selectedId === market.id
                  ? 'bg-accent-blue/10 border border-accent-blue/20'
                  : 'hover:bg-white/[0.02] border border-transparent'
              }`}
            >
              {/* Platform badge */}
              {badge && (
                <div className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${badge.color}`}>
                  <badge.icon size={12} />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <div className="text-sm text-gray-200 truncate">{market.name}</div>
                <div className="text-xs text-gray-500">
                  Vol: {market.volume}
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-sm tabular-nums font-medium text-gray-200">
                  ${market.price?.toFixed(decimals)}
                </div>
                <div
                  className={`flex items-center justify-end gap-0.5 text-xs tabular-nums ${
                    isUp ? 'text-accent-green' : 'text-accent-red'
                  }`}
                >
                  {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {isUp ? '+' : ''}{((market.change || 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
