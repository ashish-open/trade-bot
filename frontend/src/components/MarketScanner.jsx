/**
 * MarketScanner — Bloomberg-style unified watchlist across all platforms.
 * Shows all markets in a dense, sortable table with platform badges.
 */

import { useState, useMemo } from 'react'
import { Search, ArrowUpDown, Filter, Wifi } from 'lucide-react'

const PLATFORM_BADGES = {
  polymarket: { label: 'PM', class: 'badge-pm' },
  binance: { label: 'BN', class: 'badge-bn' },
  hyperliquid: { label: 'HL', class: 'badge-hl' },
}

const TYPE_LABELS = {
  prediction: 'PRED',
  spot: 'SPOT',
  perp: 'PERP',
}

export default function MarketScanner({ markets, selectedId, onSelect, activePlatform, onPlatformChange }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('volume')
  const [sortAsc, setSortAsc] = useState(false)

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
  }

  const filtered = useMemo(() => {
    let list = markets
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(
        (m) =>
          m.name.toLowerCase().includes(q) ||
          (m.symbol && m.symbol.toLowerCase().includes(q))
      )
    }
    // Sort
    list = [...list].sort((a, b) => {
      let va, vb
      if (sortKey === 'price') {
        va = a.price || 0
        vb = b.price || 0
      } else if (sortKey === 'change') {
        va = a.change || 0
        vb = b.change || 0
      } else if (sortKey === 'name') {
        va = a.name
        vb = b.name
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va)
      } else {
        // volume - parse from string like "$91.2M"
        va = parseVolume(a.volume)
        vb = parseVolume(b.volume)
      }
      return sortAsc ? va - vb : vb - va
    })
    return list
  }, [markets, search, sortKey, sortAsc])

  const platformCounts = useMemo(() => {
    const counts = { all: markets.length }
    markets.forEach((m) => {
      counts[m.platform] = (counts[m.platform] || 0) + 1
    })
    return counts
  }, [markets])

  return (
    <div className="flex flex-col h-full bg-[var(--term-panel)]">
      {/* Header */}
      <div className="term-panel-header">
        <span>Market Scanner</span>
        <span className="text-[10px] text-gray-600 font-mono">{filtered.length} mkts</span>
      </div>

      {/* Platform filter pills */}
      <div className="flex items-center gap-1 px-2 py-1.5 border-b border-white/[0.06]">
        {[
          { id: '', label: 'ALL', count: platformCounts.all },
          { id: 'polymarket', label: 'PM', count: platformCounts.polymarket || 0 },
          { id: 'binance', label: 'BN', count: platformCounts.binance || 0 },
          { id: 'hyperliquid', label: 'HL', count: platformCounts.hyperliquid || 0 },
        ].map((p) => (
          <button
            key={p.id}
            onClick={() => onPlatformChange(p.id)}
            className={`px-2 py-1 rounded text-[10px] font-semibold tracking-wider transition-all ${
              activePlatform === p.id
                ? 'bg-accent-blue/20 text-accent-blue'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
            }`}
          >
            {p.label}
            <span className="ml-1 text-gray-600">{p.count}</span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="px-2 py-1.5 border-b border-white/[0.06]">
        <div className="relative">
          <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-600" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search markets..."
            className="w-full pl-7 pr-2 py-1.5 bg-white/[0.03] border border-white/[0.06] rounded text-xs text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30"
          />
        </div>
      </div>

      {/* Column headers */}
      <div className="flex items-center px-2 py-1.5 text-[10px] uppercase tracking-wider text-gray-600 border-b border-white/[0.06] font-medium">
        <div className="w-8">SRC</div>
        <div className="flex-1 cursor-pointer hover:text-gray-400" onClick={() => handleSort('name')}>
          Market {sortKey === 'name' && (sortAsc ? '↑' : '↓')}
        </div>
        <div className="w-16 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('price')}>
          Price {sortKey === 'price' && (sortAsc ? '↑' : '↓')}
        </div>
        <div className="w-14 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('change')}>
          Chg {sortKey === 'change' && (sortAsc ? '↑' : '↓')}
        </div>
        <div className="w-16 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('volume')}>
          Vol {sortKey === 'volume' && (sortAsc ? '↑' : '↓')}
        </div>
      </div>

      {/* Market rows */}
      <div className="flex-1 overflow-y-auto">
        {filtered.map((market) => {
          const badge = PLATFORM_BADGES[market.platform]
          const isUp = (market.change || 0) >= 0
          const isSelected = selectedId === market.id
          const decimals = market.marketType === 'prediction' ? 4 : market.price > 100 ? 0 : 2

          return (
            <div
              key={market.id}
              onClick={() => onSelect(market)}
              className={`market-row flex items-center px-2 py-1.5 cursor-pointer border-b border-white/[0.02] ${
                isSelected ? 'selected' : ''
              }`}
            >
              {/* Platform badge */}
              <div className="w-8 flex-shrink-0">
                <span className={`inline-block text-[9px] font-bold px-1 py-0.5 rounded ${badge?.class || ''}`}>
                  {badge?.label || '?'}
                </span>
              </div>

              {/* Market name */}
              <div className="flex-1 min-w-0 pr-2">
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-200 truncate">{market.name}</span>
                  {market.dataSource === 'live' && (
                    <span className="flex-shrink-0 w-1 h-1 rounded-full bg-accent-green animate-pulse-glow" />
                  )}
                </div>
                {market.symbol && (
                  <span className="text-[10px] text-gray-600 mono">{market.symbol}</span>
                )}
              </div>

              {/* Price */}
              <div className="w-16 text-right">
                <span className="text-xs mono tabular-nums text-gray-200">
                  ${market.price?.toFixed(decimals)}
                </span>
              </div>

              {/* Change */}
              <div className="w-14 text-right">
                <span
                  className={`text-[11px] mono tabular-nums font-medium ${
                    isUp ? 'text-accent-green' : 'text-accent-red'
                  }`}
                >
                  {isUp ? '+' : ''}{((market.change || 0) * 100).toFixed(1)}%
                </span>
              </div>

              {/* Volume */}
              <div className="w-16 text-right">
                <span className="text-[11px] mono tabular-nums text-gray-500">
                  {market.volume || '-'}
                </span>
              </div>
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="text-center text-gray-600 text-xs py-8">No markets found</div>
        )}
      </div>
    </div>
  )
}

function parseVolume(vol) {
  if (!vol || typeof vol !== 'string') return 0
  const num = parseFloat(vol.replace('$', '').replace(',', ''))
  if (vol.includes('B')) return num * 1e9
  if (vol.includes('M')) return num * 1e6
  if (vol.includes('K')) return num * 1e3
  return num
}
