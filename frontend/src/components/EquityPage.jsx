import { useState, useEffect, useMemo, Fragment } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  Building2,
  BarChart3,
} from 'lucide-react'
import * as api from '../api'

const SECTORS = [
  'Technology',
  'Healthcare',
  'Financial Services',
  'Energy',
  'Consumer Cyclical',
  'Consumer Defensive',
  'Automotive',
]

export default function EquityPage() {
  const [equities, setEquities] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [searchText, setSearchText] = useState('')
  const [selectedSector, setSelectedSector] = useState('')
  const [expandedRows, setExpandedRows] = useState(new Set())
  const [sortConfig, setSortConfig] = useState({ key: 'symbol', direction: 'asc' })

  useEffect(() => {
    let attempts = 0
    let timer = null

    const fetchEquities = async () => {
      try {
        const data = await api.getEquityMarkets()
        const arr = Array.isArray(data) ? data : []
        setEquities(arr)
        if (arr.length > 0) {
          setLoading(false)
          // Switch to normal refresh interval
          clearTimeout(timer)
          timer = setInterval(fetchEquities, 10000)
          return
        }
      } catch (e) {
        console.error('Equity fetch error:', e)
      }
      attempts++
      if (attempts > 15) setLoading(false) // Give up after ~45s
    }

    fetchEquities()
    // Retry every 3s until data arrives, then switch to 10s
    timer = setInterval(fetchEquities, 3000)
    return () => clearInterval(timer)
  }, [])

  const filteredEquities = useMemo(() => {
    let filtered = equities

    if (activeTab === 'stocks') filtered = filtered.filter((e) => e.type === 'stock')
    else if (activeTab === 'etfs') filtered = filtered.filter((e) => e.type === 'etf')

    if (searchText) {
      const s = searchText.toLowerCase()
      filtered = filtered.filter((e) =>
        (e.symbol || '').toLowerCase().includes(s) || (e.name || '').toLowerCase().includes(s)
      )
    }

    if (selectedSector) {
      filtered = filtered.filter((e) => e.sector === selectedSector)
    }

    filtered = [...filtered].sort((a, b) => {
      let aVal = a[sortConfig.key]
      let bVal = b[sortConfig.key]
      if (aVal == null || bVal == null) return 0
      let cmp = typeof aVal === 'string' ? aVal.localeCompare(bVal) : aVal - bVal
      return sortConfig.direction === 'asc' ? cmp : -cmp
    })

    return filtered
  }, [equities, activeTab, searchText, selectedSector, sortConfig])

  const toggleRow = (sym) => {
    const next = new Set(expandedRows)
    next.has(sym) ? next.delete(sym) : next.add(sym)
    setExpandedRows(next)
  }

  const handleSort = (key) => {
    setSortConfig((prev) =>
      prev.key === key
        ? { ...prev, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
        : { key, direction: 'asc' }
    )
  }

  const changeColor = (c) => {
    if (c == null) return 'text-gray-500'
    return c >= 0 ? 'text-accent-green' : 'text-accent-red'
  }

  // API returns change as fraction (0.0004 = +0.04%)
  const changePct = (eq) => {
    const c = eq.change
    if (c == null) return null
    return c * 100
  }

  const SortHeader = ({ label, sortKey }) => (
    <button onClick={() => handleSort(sortKey)} className="flex items-center gap-1 hover:text-gray-200 transition-colors">
      {label}
      {sortConfig.key === sortKey && (
        sortConfig.direction === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
      )}
    </button>
  )

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-gray-200">Stocks & ETFs</h1>
        <p className="text-xs text-gray-500">{equities.length} equities · Real-time data via yfinance</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/[0.06]">
        {['all', 'stocks', 'etfs'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab
                ? 'text-accent-blue border-accent-blue'
                : 'text-gray-500 border-transparent hover:text-gray-300'
            }`}
          >
            {tab === 'all' ? 'All' : tab === 'stocks' ? 'Stocks' : 'ETFs'}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
          <input
            type="text"
            placeholder="Search ticker or name..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl pl-9 pr-4 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30"
          />
        </div>
        <div className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl">
          <Filter size={14} className="text-gray-500" />
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="bg-transparent text-sm text-gray-300 outline-none cursor-pointer"
          >
            <option value="">All Sectors</option>
            {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="text-xs text-gray-500">
        {filteredEquities.length} of {equities.length} equities
      </div>

      {/* Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                <th className="w-10 px-3 py-3" />
                <th className="px-4 py-3 text-left text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  <SortHeader label="Symbol" sortKey="symbol" />
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  <SortHeader label="Price" sortKey="price" />
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  Change
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  Volume
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  Day Range
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                  Sector
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {loading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-3">
                      <div className="h-5 bg-white/[0.03] rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filteredEquities.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-600">
                    No equities match your filters
                  </td>
                </tr>
              ) : (
                filteredEquities.map((eq) => {
                  const pct = changePct(eq)
                  return (
                    <Fragment key={eq.id || eq.symbol}>
                      <tr
                        className="hover:bg-white/[0.03] transition-colors cursor-pointer"
                        onClick={() => toggleRow(eq.symbol)}
                      >
                        <td className="px-3 py-3 text-gray-500">
                          {expandedRows.has(eq.symbol) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm font-semibold text-gray-200">{eq.symbol}</span>
                          {eq.type === 'etf' && (
                            <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-accent-blue/10 text-accent-blue">ETF</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400 max-w-[200px] truncate">{eq.name}</td>
                        <td className="px-4 py-3 text-right text-sm font-semibold text-gray-200 tabular-nums">
                          ${eq.price?.toFixed(2) || '—'}
                        </td>
                        <td className={`px-4 py-3 text-right text-sm font-medium tabular-nums ${changeColor(pct)}`}>
                          <div className="flex items-center justify-end gap-1">
                            {pct != null && (pct >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />)}
                            {pct != null ? `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%` : '—'}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-gray-500">{eq.volume || '—'}</td>
                        <td className="px-4 py-3 text-right text-xs text-gray-500">
                          {eq.low24h && eq.high24h
                            ? `$${eq.low24h.toFixed(2)} – $${eq.high24h.toFixed(2)}`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{eq.sector || '—'}</td>
                      </tr>

                      {expandedRows.has(eq.symbol) && (
                        <tr className="bg-white/[0.01]">
                          <td colSpan={8} className="px-6 py-4">
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <FundItem icon={Building2} label="Market Cap" value={eq.marketCap || '—'} />
                              <FundItem icon={BarChart3} label="P/E Ratio" value={eq.peRatio != null ? eq.peRatio : '—'} />
                              <FundItem icon={TrendingUp} label="EPS" value={eq.eps != null ? `$${eq.eps}` : '—'} />
                              <FundItem label="Div Yield" value={eq.dividendYield != null ? `${eq.dividendYield}%` : '—'} />
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function FundItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2">
      {Icon && <Icon size={14} className="text-accent-blue mt-0.5" />}
      <div>
        <p className="text-[10px] font-medium text-gray-600 uppercase">{label}</p>
        <p className="text-sm font-medium text-gray-300">{value}</p>
      </div>
    </div>
  )
}
