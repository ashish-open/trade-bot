import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

/**
 * MarketTickerBar — Bloomberg-style scrolling ticker at the top.
 * Displays indices, bonds, commodities, and VIX from the macro overview.
 *
 * Expects `macro` prop shaped like the backend's get_overview() response:
 * { indices: { all: [...] }, bonds: { yields: [...] }, commodities: { all: [...] }, volatility: { vix: {...} } }
 */
export default function MarketTickerBar({ macro }) {
  const [isLoading, setIsLoading] = useState(!macro)

  useEffect(() => {
    if (macro) setIsLoading(false)
  }, [macro])

  const getTickerItems = () => {
    if (!macro) return []
    const items = []

    // Indices (from indices.all array)
    const indices = macro?.indices?.all || []
    if (indices.length > 0) {
      items.push({ type: 'section', label: 'INDICES' })
      indices.forEach((m) => {
        items.push({ type: 'item', id: m.id, symbol: m.symbol || m.name, price: m.price, change: m.change, category: 'index' })
      })
    }

    // Bonds (from bonds.yields array)
    const bonds = macro?.bonds?.yields || []
    if (bonds.length > 0) {
      items.push({ type: 'section', label: 'YIELDS' })
      bonds.forEach((b) => {
        items.push({ type: 'item', id: b.id, symbol: b.maturity || b.name, price: b.yield, change: b.change, category: 'bond' })
      })
    }

    // Commodities (from commodities.all array)
    const commodities = macro?.commodities?.all || []
    if (commodities.length > 0) {
      items.push({ type: 'section', label: 'COMMODITIES' })
      commodities.forEach((c) => {
        items.push({ type: 'item', id: c.id, symbol: c.symbol || c.name, price: c.price, change: c.change, category: 'commodity' })
      })
    }

    // VIX (from volatility.vix)
    const vix = macro?.volatility?.vix
    if (vix) {
      items.push({ type: 'section', label: 'VIX' })
      items.push({ type: 'item', id: 'vol-vix', symbol: 'VIX', price: vix.value, change: vix.change, category: 'vix' })
    }

    return items
  }

  const tickerItems = getTickerItems()

  const getVixColor = (price) => {
    if (!price) return 'text-yellow-400'
    if (price >= 30) return 'text-red-500'
    if (price >= 20) return 'text-amber-400'
    return 'text-yellow-400'
  }

  const renderItem = (item, idx) => {
    if (item.type === 'section') {
      return (
        <div key={`s-${item.label}-${idx}`} className="inline-flex items-center px-3 text-[10px] font-semibold text-gray-600 tracking-wider">
          {item.label}
        </div>
      )
    }

    const change = item.change || 0
    const isUp = change >= 0
    const isVix = item.category === 'vix'
    const priceColor = isVix ? getVixColor(item.price) : 'text-gray-200'
    const changeColor = isUp ? 'text-accent-green' : 'text-accent-red'

    const formatPrice = (p) => {
      if (p == null) return '—'
      if (p >= 1000) return p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      if (p < 10) return p.toFixed(3)
      return p.toFixed(2)
    }

    return (
      <div key={`${item.id}-${idx}`} className="inline-flex items-center gap-2 px-3 py-1.5 flex-shrink-0 whitespace-nowrap">
        <span className="text-[11px] font-medium text-gray-500">{item.symbol}</span>
        {isVix && <Activity size={10} className={getVixColor(item.price)} />}
        <span className={`text-xs font-semibold tabular-nums ${priceColor}`}>
          {formatPrice(item.price)}
        </span>
        <span className={`flex items-center gap-0.5 text-[10px] tabular-nums ${changeColor}`}>
          {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          {isUp ? '+' : ''}{change.toFixed(2)}%
        </span>
      </div>
    )
  }

  if (isLoading || !macro) {
    return (
      <div className="bg-dark-800/80 backdrop-blur-xl border-b border-white/[0.04] h-10 flex items-center overflow-hidden">
        <div className="flex gap-6 px-4 w-full">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-4 bg-white/[0.03] rounded flex-shrink-0 animate-pulse" style={{ width: `${60 + Math.random() * 40}px` }} />
          ))}
        </div>
      </div>
    )
  }

  if (tickerItems.length === 0) {
    return (
      <div className="bg-dark-800/80 backdrop-blur-xl border-b border-white/[0.04] h-10 flex items-center px-4">
        <span className="text-[10px] text-gray-600">Waiting for market data...</span>
      </div>
    )
  }

  return (
    <div className="bg-dark-800/80 backdrop-blur-xl border-b border-white/[0.04] overflow-hidden">
      <div className="flex items-center h-10 ticker-scroll">
        <style>{`
          .ticker-scroll {
            animation: ticker 80s linear infinite;
          }
          @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          @media (prefers-reduced-motion: reduce) {
            .ticker-scroll { animation: none; }
          }
        `}</style>
        <div className="flex">{tickerItems.map((item, i) => renderItem(item, i))}</div>
        <div className="flex">{tickerItems.map((item, i) => renderItem(item, i + tickerItems.length))}</div>
      </div>
    </div>
  )
}
