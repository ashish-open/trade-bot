import { useState } from 'react'
import { Search, TrendingUp, TrendingDown, Target, Coins, Zap, ArrowRight } from 'lucide-react'

const PLATFORM_ICONS = { polymarket: Target, binance: Coins, hyperliquid: Zap }
const PLATFORM_COLORS = {
  polymarket: 'text-accent-purple',
  binance: 'text-accent-yellow',
  hyperliquid: 'text-accent-cyan',
}

export default function MarketsPage({ markets, activePlatform, platforms, onPlatformChange, onSelectMarket }) {
  const [search, setSearch] = useState('')

  const filtered = markets.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    (m.symbol && m.symbol.toLowerCase().includes(search.toLowerCase()))
  )

  // Group by market type for display
  const predictions = filtered.filter((m) => m.marketType === 'prediction')
  const spot = filtered.filter((m) => m.marketType === 'spot')
  const perps = filtered.filter((m) => m.marketType === 'perp')

  return (
    <div className="p-6 space-y-6">
      {/* Header with search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-200">Markets</h2>
          <p className="text-sm text-gray-500">{filtered.length} markets across {platforms.length} platforms</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search markets..."
            className="w-full pl-9 pr-3 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30 transition-colors"
          />
        </div>
      </div>

      {/* Market sections */}
      {predictions.length > 0 && (
        <MarketSection
          title="Prediction Markets"
          subtitle="Polymarket"
          icon={Target}
          color="text-accent-purple"
          markets={predictions}
          onSelect={onSelectMarket}
          isPrediction
        />
      )}

      {spot.length > 0 && (
        <MarketSection
          title="Spot Trading"
          subtitle="Binance"
          icon={Coins}
          color="text-accent-yellow"
          markets={spot}
          onSelect={onSelectMarket}
        />
      )}

      {perps.length > 0 && (
        <MarketSection
          title="Perpetuals"
          subtitle="Hyperliquid"
          icon={Zap}
          color="text-accent-cyan"
          markets={perps}
          onSelect={onSelectMarket}
          isPerp
        />
      )}
    </div>
  )
}

function MarketSection({ title, subtitle, icon: Icon, color, markets, onSelect, isPrediction, isPerp }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={16} className={color} />
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
        <span className="text-xs text-gray-600">— {subtitle}</span>
        <span className="ml-auto text-xs text-gray-600">{markets.length} markets</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-white/5">
              <th className="text-left pb-3 pr-4">{isPrediction ? 'Market' : 'Pair'}</th>
              <th className="text-right pb-3 pr-4">Price</th>
              <th className="text-right pb-3 pr-4">24h Change</th>
              <th className="text-right pb-3 pr-4">Volume</th>
              {isPerp && <th className="text-right pb-3 pr-4">Funding</th>}
              {isPerp && <th className="text-right pb-3 pr-4">Max Leverage</th>}
              {isPrediction && <th className="text-right pb-3 pr-4">End Date</th>}
              <th className="text-center pb-3">Trade</th>
            </tr>
          </thead>
          <tbody>
            {markets.map((m) => {
              const changeUp = (m.change || 0) >= 0
              const decimals = isPrediction ? 4 : 2
              return (
                <tr
                  key={m.id}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-3 pr-4">
                    <div className="font-medium text-gray-200">{m.name}</div>
                    {m.symbol && !isPrediction && (
                      <div className="text-xs text-gray-500">{m.description}</div>
                    )}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-gray-200 font-medium">
                    ${m.price?.toFixed(decimals)}
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <span className={`flex items-center justify-end gap-0.5 tabular-nums ${
                      changeUp ? 'text-accent-green' : 'text-accent-red'
                    }`}>
                      {changeUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {changeUp ? '+' : ''}{((m.change || 0) * 100).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-gray-400">
                    {m.volume}
                  </td>
                  {isPerp && (
                    <td className={`py-3 pr-4 text-right tabular-nums ${
                      (m.fundingRate || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'
                    }`}>
                      {((m.fundingRate || 0) * 100).toFixed(4)}%
                    </td>
                  )}
                  {isPerp && (
                    <td className="py-3 pr-4 text-right tabular-nums text-gray-400">
                      {m.leverageMax}x
                    </td>
                  )}
                  {isPrediction && (
                    <td className="py-3 pr-4 text-right text-xs text-gray-500">
                      {m.endDate}
                    </td>
                  )}
                  <td className="py-3 text-center">
                    <button
                      onClick={() => onSelect(m)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-accent-blue/10 text-accent-blue hover:bg-accent-blue/20 border border-accent-blue/20 transition-all flex items-center gap-1 mx-auto"
                    >
                      Trade <ArrowRight size={10} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
