import { useEffect, useState } from 'react'
import {
  Globe,
  TrendingUp,
  TrendingDown,
  Activity,
  Landmark,
  Flame,
  Gem,
  DollarSign,
  AlertTriangle,
  BarChart3,
} from 'lucide-react'
import * as api from '../api'

export default function MacroPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await api.getMacroOverview()
        setData(response)
        setError(null)
      } catch (err) {
        setError(err.message || 'Failed to fetch macro data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !data) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <Globe className="w-8 h-8 text-accent-blue" />
          <h1 className="text-2xl font-semibold text-gray-200">Economy</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass p-5 animate-pulse">
              <div className="h-4 bg-white/5 rounded w-1/2 mb-3" />
              <div className="h-8 bg-white/5 rounded w-2/3 mb-2" />
              <div className="h-4 bg-white/5 rounded w-1/3" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="p-6 text-center text-accent-red">{error}</div>
    )
  }

  // Parse the nested backend structure
  const vixData = data?.volatility?.vix || {}
  const vixValue = vixData?.value || 0
  const vixChange = vixData?.change || 0
  const marketCondition = data?.volatility?.market_condition || 'unknown'

  const allIndices = data?.indices?.all || []
  const bondsData = data?.bonds?.yields || []
  const yieldCurve = data?.bonds?.yield_curve || {}
  const allCommodities = data?.commodities?.all || []

  // Group indices by region
  const regionMap = {
    'US': ['US Large Cap', 'US Tech', 'US Small Cap'],
    'Europe': ['UK Large Cap', 'Germany', 'Eurozone'],
    'Asia': ['Japan', 'Hong Kong'],
  }

  const groupedIndices = {}
  for (const [region, categories] of Object.entries(regionMap)) {
    groupedIndices[region] = allIndices.filter(idx => categories.includes(idx.category))
  }

  const getSentimentColor = (v) => {
    if (v < 15) return 'text-accent-green'
    if (v < 25) return 'text-accent-yellow'
    if (v < 35) return 'text-orange-400'
    return 'text-accent-red'
  }

  const getSentimentLabel = (v) => {
    if (v < 15) return 'Low Fear'
    if (v < 25) return 'Moderate'
    if (v < 35) return 'Elevated'
    return 'Extreme Fear'
  }

  const getSentimentBg = (v) => {
    if (v < 15) return 'from-green-900/20 to-green-900/5'
    if (v < 25) return 'from-yellow-900/20 to-yellow-900/5'
    if (v < 35) return 'from-orange-900/20 to-orange-900/5'
    return 'from-red-900/20 to-red-900/5'
  }

  const getCommodityIcon = (name) => {
    const n = (name || '').toLowerCase()
    if (n.includes('gold') || n.includes('silver')) return <Gem size={18} />
    if (n.includes('oil') || n.includes('gas')) return <Flame size={18} />
    return <DollarSign size={18} />
  }

  const ChangeIndicator = ({ value }) => {
    if (value == null) return null
    const pos = value >= 0
    return (
      <span className={`flex items-center gap-1 text-sm ${pos ? 'text-accent-green' : 'text-accent-red'}`}>
        {pos ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {pos ? '+' : ''}{value.toFixed(2)}%
      </span>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Globe size={24} className="text-accent-blue" />
        <div>
          <h1 className="text-xl font-semibold text-gray-200">Economy & Macro</h1>
          <p className="text-xs text-gray-500">Global indices, bonds, commodities, and volatility</p>
        </div>
      </div>

      {/* VIX / Market Sentiment Banner */}
      <div className={`glass p-5 bg-gradient-to-r ${getSentimentBg(vixValue)}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity size={16} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-300">Market Volatility (VIX)</span>
            </div>
            <p className="text-xs text-gray-500">S&P 500 Implied Volatility Index</p>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold tabular-nums ${getSentimentColor(vixValue)}`}>
              {vixValue.toFixed(2)}
            </div>
            <div className={`text-sm font-medium ${getSentimentColor(vixValue)}`}>
              {getSentimentLabel(vixValue)}
            </div>
            <ChangeIndicator value={vixChange} />
          </div>
        </div>
      </div>

      {/* Global Indices */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={16} className="text-accent-blue" />
          <h2 className="text-sm font-medium text-gray-300">Global Indices</h2>
        </div>
        <div className="space-y-4">
          {Object.entries(groupedIndices).map(([region, indices]) => (
            indices.length > 0 && (
              <div key={region}>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{region}</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {indices.map((idx) => (
                    <div key={idx.id} className="glass p-4 hover:bg-white/[0.04] transition-colors">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-300">{idx.name}</span>
                        <span className="text-xs text-gray-600">{idx.symbol}</span>
                      </div>
                      <div className="text-xl font-semibold text-gray-100 tabular-nums">
                        {idx.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <ChangeIndicator value={idx.change} />
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Treasury Yields */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Landmark size={16} className="text-accent-blue" />
          <h2 className="text-sm font-medium text-gray-300">Treasury Yields</h2>
          {yieldCurve.is_inverted && (
            <span className="ml-auto flex items-center gap-1 text-xs bg-accent-red/10 text-accent-red px-2 py-1 rounded-lg border border-accent-red/20">
              <AlertTriangle size={12} />
              Yield Curve Inverted
            </span>
          )}
        </div>
        <div className="glass p-5 space-y-4">
          {bondsData.map((bond) => (
            <div key={bond.id} className="space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">{bond.name}</span>
                <div className="flex items-center gap-3">
                  <ChangeIndicator value={bond.change} />
                  <span className="text-lg font-semibold text-accent-green tabular-nums">
                    {(bond.yield || 0).toFixed(3)}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-white/5 rounded-full h-1.5">
                <div
                  className="bg-gradient-to-r from-accent-blue to-accent-cyan h-full rounded-full transition-all"
                  style={{ width: `${Math.min((bond.yield || 0) * 10, 100)}%` }}
                />
              </div>
            </div>
          ))}
          {yieldCurve.spread_10y_5y != null && (
            <div className="pt-2 border-t border-white/[0.04]">
              <span className="text-xs text-gray-500">
                10Y–5Y Spread: <span className={yieldCurve.is_inverted ? 'text-accent-red' : 'text-accent-green'}>
                  {yieldCurve.spread_10y_5y > 0 ? '+' : ''}{yieldCurve.spread_10y_5y.toFixed(3)}%
                </span>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Commodities */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Flame size={16} className="text-accent-yellow" />
          <h2 className="text-sm font-medium text-gray-300">Commodities</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {allCommodities.map((cmd) => (
            <div key={cmd.id} className="glass p-4 hover:bg-white/[0.04] transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-300">{cmd.name}</span>
                <span className="text-gray-500">{getCommodityIcon(cmd.name)}</span>
              </div>
              <div className="text-xl font-semibold text-gray-100 tabular-nums mb-1">
                ${cmd.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="flex items-center justify-between">
                <ChangeIndicator value={cmd.change} />
                <span className="text-xs text-gray-600">{cmd.unit}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-600 pt-2">
        Data refreshes every 15 seconds · Last: {new Date().toLocaleTimeString()}
      </div>
    </div>
  )
}
