/**
 * PortfolioPanel — Bloomberg-style right sidebar showing
 * account stats, positions, exposure breakdown, and risk metrics.
 */

import { useState } from 'react'
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from 'lucide-react'

export default function PortfolioPanel({ portfolio, positions, onClose, trades }) {
  const [tab, setTab] = useState('positions') // positions | trades | exposure

  const pnlColor = portfolio.totalPnl >= 0 ? 'text-accent-green' : 'text-accent-red'
  const dayColor = portfolio.dayPnl >= 0 ? 'text-accent-green' : 'text-accent-red'

  // Calculate exposure by platform
  const exposure = {}
  let totalExposure = 0
  ;(positions || []).forEach((p) => {
    const cost = Math.abs(p.size * p.entryPrice)
    exposure[p.platform] = (exposure[p.platform] || 0) + cost
    totalExposure += cost
  })

  return (
    <div className="flex flex-col h-full bg-[var(--term-panel)]">
      {/* Header */}
      <div className="term-panel-header">
        <span>Portfolio</span>
        <span className="text-[10px] text-gray-600 font-mono">PAPER</span>
      </div>

      {/* Account stats */}
      <div className="px-3 py-2 border-b border-white/[0.06] space-y-1.5">
        <div className="flex justify-between items-baseline">
          <span className="text-[10px] text-gray-600 uppercase tracking-wider">Net Value</span>
          <span className="text-lg font-bold mono tabular-nums text-gray-100">
            ${(portfolio.totalValue || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-[10px] text-gray-600 uppercase tracking-wider">Cash</span>
          <span className="text-sm mono tabular-nums text-gray-300">
            ${(portfolio.cash || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        {/* P&L row */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
            <div className="text-[9px] text-gray-600 uppercase">Total P&L</div>
            <div className={`text-sm font-bold mono tabular-nums ${pnlColor}`}>
              {portfolio.totalPnl >= 0 ? '+' : ''}${(portfolio.totalPnl || 0).toFixed(2)}
            </div>
            <div className={`text-[10px] mono ${pnlColor}`}>
              {portfolio.totalPnlPercent >= 0 ? '+' : ''}{(portfolio.totalPnlPercent || 0).toFixed(2)}%
            </div>
          </div>
          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
            <div className="text-[9px] text-gray-600 uppercase">Day P&L</div>
            <div className={`text-sm font-bold mono tabular-nums ${dayColor}`}>
              {portfolio.dayPnl >= 0 ? '+' : ''}${(portfolio.dayPnl || 0).toFixed(2)}
            </div>
            <div className={`text-[10px] mono ${dayColor}`}>
              {portfolio.dayPnlPercent >= 0 ? '+' : ''}{(portfolio.dayPnlPercent || 0).toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex gap-3 text-[10px] mono pt-0.5">
          <span className="text-gray-500">Win: <span className="text-gray-300">{portfolio.winRate || 0}%</span></span>
          <span className="text-gray-500">Trades: <span className="text-gray-300">{portfolio.totalTrades || 0}</span></span>
          <span className="text-gray-500">Open: <span className="text-gray-300">{positions?.length || 0}</span></span>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex border-b border-white/[0.06]">
        {[
          { id: 'positions', label: 'Positions', count: positions?.length || 0 },
          { id: 'trades', label: 'Trades', count: trades?.length || 0 },
          { id: 'exposure', label: 'Exposure' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 py-2 text-[10px] font-medium uppercase tracking-wider transition-all ${
              tab === t.id
                ? 'text-accent-blue border-b-2 border-accent-blue'
                : 'text-gray-600 hover:text-gray-400'
            }`}
          >
            {t.label}
            {t.count !== undefined && <span className="ml-1 text-gray-700">{t.count}</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'positions' && (
          <div>
            {(!positions || positions.length === 0) ? (
              <div className="text-center text-gray-600 text-xs py-8">No open positions</div>
            ) : (
              positions.map((pos) => {
                const isProfit = pos.pnl >= 0
                const decimals = pos.entryPrice > 10 ? 2 : 4
                return (
                  <div
                    key={pos.id}
                    className="px-3 py-2 border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className={`text-[9px] font-bold px-1 py-0.5 rounded ${
                          pos.platform === 'polymarket' ? 'badge-pm' :
                          pos.platform === 'binance' ? 'badge-bn' : 'badge-hl'
                        }`}>
                          {pos.platform === 'polymarket' ? 'PM' : pos.platform === 'binance' ? 'BN' : 'HL'}
                        </span>
                        <span className="text-xs text-gray-200 truncate">{pos.market}</span>
                      </div>
                      <button
                        onClick={() => onClose(pos)}
                        className="text-[9px] px-1.5 py-0.5 rounded bg-accent-red/10 text-accent-red hover:bg-accent-red/20 transition-colors flex-shrink-0 ml-2"
                      >
                        CLOSE
                      </button>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <div className="flex items-center gap-2 text-[10px] mono">
                        <span className={`font-medium ${pos.side === 'YES' || pos.side === 'LONG' ? 'text-accent-green' : 'text-accent-red'}`}>
                          {pos.side}
                        </span>
                        <span className="text-gray-500">{pos.size}</span>
                        <span className="text-gray-600">@</span>
                        <span className="text-gray-400">${pos.entryPrice.toFixed(decimals)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {isProfit ? (
                          <ArrowUpRight size={10} className="text-accent-green" />
                        ) : (
                          <ArrowDownRight size={10} className="text-accent-red" />
                        )}
                        <span className={`text-xs mono tabular-nums font-medium ${isProfit ? 'text-accent-green' : 'text-accent-red'}`}>
                          {isProfit ? '+' : ''}${pos.pnl.toFixed(2)}
                        </span>
                        <span className={`text-[10px] mono ${isProfit ? 'text-accent-green/60' : 'text-accent-red/60'}`}>
                          {isProfit ? '+' : ''}{pos.pnlPercent.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}

        {tab === 'trades' && (
          <div>
            {(!trades || trades.length === 0) ? (
              <div className="text-center text-gray-600 text-xs py-8">No trades yet</div>
            ) : (
              trades.slice(0, 20).map((trade) => (
                <div
                  key={trade.id}
                  className="px-3 py-1.5 border-b border-white/[0.03] hover:bg-white/[0.02]"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[9px] font-bold px-1 py-0.5 rounded ${
                        trade.side === 'BUY' ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'
                      }`}>
                        {trade.side}
                      </span>
                      <span className="text-xs text-gray-300 truncate max-w-[150px]">{trade.market}</span>
                    </div>
                    {trade.pnl !== null && trade.pnl !== undefined && (
                      <span className={`text-[10px] mono tabular-nums ${trade.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] mono text-gray-600">
                    <span>{trade.size} @ ${trade.price?.toFixed(trade.price > 10 ? 2 : 4)}</span>
                    <span>{trade.time}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === 'exposure' && (
          <div className="p-3 space-y-3">
            {totalExposure === 0 ? (
              <div className="text-center text-gray-600 text-xs py-8">No exposure</div>
            ) : (
              <>
                {/* Platform exposure bars */}
                {Object.entries(exposure).map(([platform, amount]) => {
                  const pct = (amount / totalExposure) * 100
                  const colorClass = platform === 'polymarket' ? 'bg-accent-purple' : platform === 'binance' ? 'bg-accent-yellow' : 'bg-accent-cyan'
                  return (
                    <div key={platform}>
                      <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-gray-400 uppercase">{platform}</span>
                        <span className="mono text-gray-300">${amount.toFixed(2)} ({pct.toFixed(1)}%)</span>
                      </div>
                      <div className="h-2 bg-white/[0.04] rounded overflow-hidden">
                        <div className={`h-full ${colorClass} rounded transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}

                {/* Summary */}
                <div className="pt-2 border-t border-white/[0.06] space-y-1.5 text-[10px] mono">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Exposure</span>
                    <span className="text-gray-300">${totalExposure.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Cash Reserve</span>
                    <span className="text-gray-300">${(portfolio.cash || 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Utilization</span>
                    <span className={totalExposure / (portfolio.totalValue || 1) > 0.8 ? 'text-accent-red' : 'text-gray-300'}>
                      {((totalExposure / (portfolio.totalValue || 1)) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
