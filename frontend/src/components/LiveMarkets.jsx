import { Search, TrendingUp, TrendingDown } from 'lucide-react'
import { useState } from 'react'

export default function LiveMarkets({ markets }) {
  const [search, setSearch] = useState('')

  const filtered = markets.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Live Markets</h3>
        <div className="flex items-center gap-1 w-2 h-2">
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
      <div className="space-y-1">
        {filtered.map((market) => {
          const isUp = market.change >= 0
          return (
            <div
              key={market.id}
              className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors cursor-pointer"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm text-gray-200 truncate">{market.name}</div>
                <div className="text-xs text-gray-500">Vol: {market.volume}</div>
              </div>
              <div className="text-right">
                <div className="text-sm tabular-nums font-medium text-gray-200">
                  ${market.price.toFixed(2)}
                </div>
                <div
                  className={`flex items-center justify-end gap-0.5 text-xs tabular-nums ${
                    isUp ? 'text-accent-green' : 'text-accent-red'
                  }`}
                >
                  {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {isUp ? '+' : ''}{(market.change * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
