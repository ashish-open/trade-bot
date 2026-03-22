/**
 * TerminalPanel — Bloomberg-style slide-out terminal that overlays
 * the main dashboard. Contains MarketScanner + quick orderbook + trade.
 */

import { useState, useMemo } from 'react'
import { X, Search, ArrowUpDown, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, ShoppingCart } from 'lucide-react'

const PLATFORM_BADGES = {
  polymarket: { label: 'PM', class: 'badge-pm' },
  binance: { label: 'BN', class: 'badge-bn' },
  hyperliquid: { label: 'HL', class: 'badge-hl' },
}

function parseVolume(vol) {
  if (!vol || typeof vol !== 'string') return 0
  const num = parseFloat(vol.replace('$', '').replace(',', ''))
  if (vol.includes('B')) return num * 1e9
  if (vol.includes('M')) return num * 1e6
  if (vol.includes('K')) return num * 1e3
  return num
}

export default function TerminalPanel({
  open,
  onClose,
  markets,
  allMarkets,
  selectedMarket,
  onSelectMarket,
  orderBook,
  portfolio,
  positions,
  trades,
  onPlaceOrder,
  onClosePosition,
}) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('volume')
  const [sortAsc, setSortAsc] = useState(false)
  const [platformFilter, setPlatformFilter] = useState('')
  const [tab, setTab] = useState('scanner') // scanner | portfolio

  const handleSort = (key) => {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(false) }
  }

  const displayMarkets = useMemo(() => {
    let list = allMarkets || []
    if (platformFilter) list = list.filter((m) => m.platform === platformFilter)
    if (search) {
      const q = search.toLowerCase()
      list = list.filter((m) =>
        m.name.toLowerCase().includes(q) ||
        (m.symbol && m.symbol.toLowerCase().includes(q))
      )
    }
    list = [...list].sort((a, b) => {
      let va, vb
      if (sortKey === 'price') { va = a.price || 0; vb = b.price || 0 }
      else if (sortKey === 'change') { va = a.change || 0; vb = b.change || 0 }
      else if (sortKey === 'name') return sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
      else { va = parseVolume(a.volume); vb = parseVolume(b.volume) }
      return sortAsc ? va - vb : vb - va
    })
    return list
  }, [allMarkets, platformFilter, search, sortKey, sortAsc])

  const platformCounts = useMemo(() => {
    const c = { all: (allMarkets || []).length }
    ;(allMarkets || []).forEach((m) => { c[m.platform] = (c[m.platform] || 0) + 1 })
    return c
  }, [allMarkets])

  // Exposure by platform
  const exposure = useMemo(() => {
    const exp = {}
    let total = 0
    ;(positions || []).forEach((p) => {
      const cost = Math.abs(p.size * p.entryPrice)
      exp[p.platform] = (exp[p.platform] || 0) + cost
      total += cost
    })
    return { byPlatform: exp, total }
  }, [positions])

  const isPrediction = selectedMarket?.marketType === 'prediction'
  const decimals = isPrediction ? 4 : (selectedMarket?.price || 0) > 100 ? 0 : 2

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[80] flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Terminal panel */}
      <div className="w-[900px] max-w-[90vw] h-full bg-[#0a0a0f] border-l border-white/[0.08] flex flex-col animate-slide-in overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.08] bg-[#0f1017]">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-accent-blue tracking-wider">TERMINAL</span>
            <div className="flex items-center gap-1">
              {[
                { id: 'scanner', label: 'SCANNER' },
                { id: 'portfolio', label: 'PORTFOLIO' },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`px-2 py-1 rounded text-[10px] font-semibold tracking-wider transition-all ${
                    tab === t.id ? 'bg-accent-blue/15 text-accent-blue' : 'text-gray-600 hover:text-gray-400'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <span className="text-[10px] mono text-gray-600">{(allMarkets || []).length} mkts</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-white/[0.06] text-gray-500 hover:text-gray-300">
            <X size={16} />
          </button>
        </div>

        {tab === 'scanner' ? (
          <div className="flex flex-1 min-h-0 overflow-hidden">
            {/* Left: Market list */}
            <div className="w-[380px] flex flex-col border-r border-white/[0.06] overflow-hidden">
              {/* Platform pills */}
              <div className="flex items-center gap-1 px-2 py-1.5 border-b border-white/[0.06]">
                {[
                  { id: '', label: 'ALL', count: platformCounts.all },
                  { id: 'polymarket', label: 'PM', count: platformCounts.polymarket || 0 },
                  { id: 'binance', label: 'BN', count: platformCounts.binance || 0 },
                  { id: 'hyperliquid', label: 'HL', count: platformCounts.hyperliquid || 0 },
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPlatformFilter(p.id)}
                    className={`px-2 py-1 rounded text-[10px] font-semibold tracking-wider transition-all ${
                      platformFilter === p.id
                        ? 'bg-accent-blue/20 text-accent-blue'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
                    }`}
                  >
                    {p.label} <span className="text-gray-600">{p.count}</span>
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
              <div className="flex items-center px-2 py-1 text-[9px] uppercase tracking-wider text-gray-600 border-b border-white/[0.06] font-medium">
                <div className="w-7">SRC</div>
                <div className="flex-1 cursor-pointer hover:text-gray-400" onClick={() => handleSort('name')}>Market</div>
                <div className="w-16 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('price')}>Price</div>
                <div className="w-12 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('change')}>Chg</div>
                <div className="w-14 text-right cursor-pointer hover:text-gray-400" onClick={() => handleSort('volume')}>Vol</div>
              </div>

              {/* Market rows */}
              <div className="flex-1 overflow-y-auto">
                {displayMarkets.map((market) => {
                  const badge = PLATFORM_BADGES[market.platform]
                  const isUp = (market.change || 0) >= 0
                  const isSelected = selectedMarket?.id === market.id
                  const dec = market.marketType === 'prediction' ? 4 : market.price > 100 ? 0 : 2
                  return (
                    <div
                      key={market.id}
                      onClick={() => onSelectMarket(market)}
                      className={`market-row flex items-center px-2 py-1.5 cursor-pointer border-b border-white/[0.02] ${isSelected ? 'selected' : ''}`}
                    >
                      <div className="w-7 flex-shrink-0">
                        <span className={`text-[8px] font-bold px-1 py-0.5 rounded ${badge?.class || ''}`}>{badge?.label || '?'}</span>
                      </div>
                      <div className="flex-1 min-w-0 pr-1">
                        <div className="flex items-center gap-1">
                          <span className="text-[11px] text-gray-200 truncate">{market.name}</span>
                          {market.dataSource === 'live' && <span className="w-1 h-1 rounded-full bg-accent-green flex-shrink-0" />}
                        </div>
                        {market.symbol && <span className="text-[9px] text-gray-600 mono">{market.symbol}</span>}
                      </div>
                      <div className="w-16 text-right text-[11px] mono tabular-nums text-gray-200">${market.price?.toFixed(dec)}</div>
                      <div className={`w-12 text-right text-[10px] mono tabular-nums font-medium ${isUp ? 'text-accent-green' : 'text-accent-red'}`}>
                        {isUp ? '+' : ''}{((market.change || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="w-14 text-right text-[10px] mono tabular-nums text-gray-500">{market.volume || '-'}</div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: Selected market detail + orderbook */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {selectedMarket ? (
                <>
                  {/* Market header */}
                  <div className="px-3 py-2 border-b border-white/[0.06] flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${PLATFORM_BADGES[selectedMarket.platform]?.class || ''}`}>
                          {PLATFORM_BADGES[selectedMarket.platform]?.label || '?'}
                        </span>
                        <span className="text-xs text-gray-300 font-medium">{selectedMarket.name}</span>
                        {selectedMarket.dataSource === 'live' ? (
                          <span className="badge-live text-[8px] font-bold px-1 py-0.5 rounded">LIVE</span>
                        ) : (
                          <span className="badge-sim text-[8px] font-bold px-1 py-0.5 rounded">SIM</span>
                        )}
                      </div>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-xl font-bold mono tabular-nums text-gray-100">${selectedMarket.price?.toFixed(decimals)}</span>
                        <span className={`text-sm mono tabular-nums ${(selectedMarket.change || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                          {(selectedMarket.change || 0) >= 0 ? '+' : ''}{((selectedMarket.change || 0) * 100).toFixed(2)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-right text-[10px] mono text-gray-500">
                      <div>Vol: {selectedMarket.volume}</div>
                      <div>{selectedMarket.category}</div>
                    </div>
                  </div>

                  {/* Orderbook */}
                  <div className="flex-1 overflow-y-auto px-3 py-2">
                    <div className="text-[10px] uppercase tracking-wider text-gray-600 font-medium mb-2">Order Book</div>
                    {(orderBook?.bids?.length || orderBook?.asks?.length) ? (
                      <div className="space-y-0.5">
                        <div className="flex text-[9px] uppercase tracking-wider text-gray-700 mb-1">
                          <span className="flex-1">Size</span>
                          <span className="w-16 text-center">Bid</span>
                          <span className="w-3" />
                          <span className="w-16 text-center">Ask</span>
                          <span className="flex-1 text-right">Size</span>
                        </div>
                        {Array.from({ length: Math.max(orderBook.bids?.length || 0, orderBook.asks?.length || 0, 8) }).map((_, i) => {
                          const bid = orderBook.bids?.[i]
                          const ask = orderBook.asks?.[i]
                          const maxSize = Math.max(...(orderBook.bids || []).map(b => b.size), ...(orderBook.asks || []).map(a => a.size), 1)
                          return (
                            <div key={i} className="flex items-center text-[11px] h-5">
                              <div className="flex-1 relative">
                                {bid && (
                                  <>
                                    <div className="absolute right-0 top-0 bottom-0 bg-accent-green/[0.06] rounded-l" style={{ width: `${(bid.size / maxSize) * 100}%` }} />
                                    <span className="relative mono tabular-nums text-gray-400 text-[10px]">{bid.size.toLocaleString()}</span>
                                  </>
                                )}
                              </div>
                              <span className="w-16 text-center mono tabular-nums font-medium text-accent-green text-[10px]">
                                {bid ? bid.price.toFixed(isPrediction ? 3 : 2) : ''}
                              </span>
                              <span className="w-3 text-center text-gray-800">|</span>
                              <span className="w-16 text-center mono tabular-nums font-medium text-accent-red text-[10px]">
                                {ask ? ask.price.toFixed(isPrediction ? 3 : 2) : ''}
                              </span>
                              <div className="flex-1 relative text-right">
                                {ask && (
                                  <>
                                    <div className="absolute left-0 top-0 bottom-0 bg-accent-red/[0.06] rounded-r" style={{ width: `${(ask.size / maxSize) * 100}%` }} />
                                    <span className="relative mono tabular-nums text-gray-400 text-[10px]">{ask.size.toLocaleString()}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          )
                        })}
                        {orderBook.bids?.[0] && orderBook.asks?.[0] && (
                          <div className="text-[9px] text-gray-600 flex justify-center gap-4 mono pt-1 border-t border-white/[0.04]">
                            <span>Spread: ${(orderBook.asks[0].price - orderBook.bids[0].price).toFixed(isPrediction ? 3 : 2)}</span>
                            <span>Mid: ${((orderBook.asks[0].price + orderBook.bids[0].price) / 2).toFixed(isPrediction ? 4 : 3)}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-gray-600 text-xs py-4 text-center">No orderbook data</div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-600 text-xs">
                  Select a market from the scanner
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Portfolio tab */
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded bg-white/[0.03] border border-white/[0.06]">
                <div className="text-[9px] text-gray-600 uppercase tracking-wider">Net Value</div>
                <div className="text-lg font-bold mono tabular-nums text-gray-100">${(portfolio.totalValue || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              </div>
              <div className="p-3 rounded bg-white/[0.03] border border-white/[0.06]">
                <div className="text-[9px] text-gray-600 uppercase tracking-wider">Total P&L</div>
                <div className={`text-lg font-bold mono tabular-nums ${portfolio.totalPnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {portfolio.totalPnl >= 0 ? '+' : ''}${(portfolio.totalPnl || 0).toFixed(2)}
                </div>
              </div>
              <div className="p-3 rounded bg-white/[0.03] border border-white/[0.06]">
                <div className="text-[9px] text-gray-600 uppercase tracking-wider">Win Rate</div>
                <div className="text-lg font-bold mono tabular-nums text-gray-100">{portfolio.winRate || 0}%</div>
                <div className="text-[10px] text-gray-600 mono">{portfolio.totalTrades || 0} trades</div>
              </div>
            </div>

            {/* Positions */}
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold mb-2">
                Open Positions ({positions?.length || 0})
              </div>
              {(!positions || positions.length === 0) ? (
                <div className="text-gray-600 text-xs py-4 text-center">No open positions</div>
              ) : (
                <div className="space-y-1">
                  {positions.map((pos) => (
                    <div key={pos.id} className="flex items-center justify-between px-3 py-2 rounded bg-white/[0.02] border border-white/[0.04]">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`text-[8px] font-bold px-1 py-0.5 rounded ${PLATFORM_BADGES[pos.platform]?.class || ''}`}>
                          {PLATFORM_BADGES[pos.platform]?.label || '?'}
                        </span>
                        <div className="min-w-0">
                          <div className="text-xs text-gray-200 truncate max-w-[200px]">{pos.market}</div>
                          <div className="text-[10px] mono text-gray-500">{pos.side} {pos.size} @ ${pos.entryPrice.toFixed(pos.entryPrice > 10 ? 2 : 4)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className={`text-xs mono tabular-nums font-medium ${pos.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                            {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                          </div>
                          <div className={`text-[10px] mono ${pos.pnl >= 0 ? 'text-accent-green/60' : 'text-accent-red/60'}`}>
                            {pos.pnlPercent >= 0 ? '+' : ''}{pos.pnlPercent.toFixed(1)}%
                          </div>
                        </div>
                        <button
                          onClick={() => onClosePosition(pos)}
                          className="text-[9px] px-2 py-1 rounded bg-accent-red/10 text-accent-red hover:bg-accent-red/20"
                        >
                          CLOSE
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Exposure */}
            {exposure.total > 0 && (
              <div>
                <div className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold mb-2">Exposure by Platform</div>
                {Object.entries(exposure.byPlatform).map(([platform, amount]) => {
                  const pct = (amount / exposure.total) * 100
                  const barColor = platform === 'polymarket' ? 'bg-accent-purple' : platform === 'binance' ? 'bg-accent-yellow' : 'bg-accent-cyan'
                  return (
                    <div key={platform} className="mb-2">
                      <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-gray-400 uppercase">{platform}</span>
                        <span className="mono text-gray-300">${amount.toFixed(2)} ({pct.toFixed(1)}%)</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.04] rounded overflow-hidden">
                        <div className={`h-full ${barColor} rounded`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
                <div className="flex justify-between text-[10px] mono text-gray-500 mt-2 pt-2 border-t border-white/[0.06]">
                  <span>Utilization</span>
                  <span className={exposure.total / (portfolio.totalValue || 1) > 0.8 ? 'text-accent-red' : ''}>
                    {((exposure.total / (portfolio.totalValue || 1)) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            )}

            {/* Recent trades */}
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold mb-2">Recent Trades</div>
              {(!trades || trades.length === 0) ? (
                <div className="text-gray-600 text-xs py-4 text-center">No trades yet</div>
              ) : (
                <div className="space-y-0.5">
                  {trades.slice(0, 15).map((t) => (
                    <div key={t.id} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-white/[0.02]">
                      <div className="flex items-center gap-2">
                        <span className={`text-[8px] font-bold px-1 py-0.5 rounded ${t.side === 'BUY' ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'}`}>
                          {t.side}
                        </span>
                        <span className="text-[11px] text-gray-300 truncate max-w-[200px]">{t.market}</span>
                        <span className="text-[10px] mono text-gray-600">{t.size} @ ${t.price?.toFixed(t.price > 10 ? 2 : 4)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {t.pnl !== null && t.pnl !== undefined && (
                          <span className={`text-[10px] mono tabular-nums ${t.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                            {t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}
                          </span>
                        )}
                        <span className="text-[9px] mono text-gray-700">{t.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
