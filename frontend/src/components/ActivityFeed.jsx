/**
 * ActivityFeed — Bloomberg-style bottom ticker showing
 * recent trades, order fills, and system events.
 */

import { ArrowUpRight, ArrowDownRight, AlertCircle, CheckCircle2, X, Clock } from 'lucide-react'

export default function ActivityFeed({ trades, openOrders, onCancelOrder }) {
  // Combine trades and orders into a unified feed, newest first
  const items = []

  ;(trades || []).slice(0, 10).forEach((t) => {
    items.push({
      id: `trade-${t.id}`,
      type: 'trade',
      side: t.side,
      market: t.market,
      size: t.size,
      price: t.price,
      pnl: t.pnl,
      time: t.time,
      status: t.status,
    })
  })

  ;(openOrders || []).forEach((o) => {
    items.push({
      id: `order-${o.id}`,
      orderId: o.id,
      type: 'order',
      side: o.side,
      market: o.market,
      size: o.size,
      price: o.price,
      orderType: o.type,
      time: o.createdAt?.slice(11, 19) || '',
    })
  })

  return (
    <div className="flex flex-col bg-[var(--term-panel)] border-t border-white/[0.06]">
      <div className="flex items-center justify-between px-3 py-1 border-b border-white/[0.04]">
        <span className="text-[10px] uppercase tracking-wider text-gray-600 font-semibold">Activity Feed</span>
        <div className="flex items-center gap-3 text-[10px] text-gray-600">
          <span className="mono">{trades?.length || 0} fills</span>
          <span className="mono">{openOrders?.length || 0} pending</span>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        <div className="flex items-stretch min-w-0 h-full">
          {items.length === 0 ? (
            <div className="flex items-center px-4 text-gray-600 text-xs">
              No activity yet — place your first trade
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-2 px-3 py-1.5 border-r border-white/[0.04] flex-shrink-0 hover:bg-white/[0.02]"
              >
                {/* Side badge */}
                <span className={`text-[9px] font-bold px-1 py-0.5 rounded ${
                  item.side === 'BUY' || item.side === 'buy'
                    ? 'bg-accent-green/10 text-accent-green'
                    : 'bg-accent-red/10 text-accent-red'
                }`}>
                  {(item.side || '').toUpperCase()}
                </span>

                {/* Market */}
                <span className="text-[11px] text-gray-300 max-w-[150px] truncate">{item.market}</span>

                {/* Details */}
                <span className="text-[10px] mono text-gray-500">
                  {item.size} @ ${item.price?.toFixed(item.price > 10 ? 2 : 4)}
                </span>

                {/* P&L for fills */}
                {item.type === 'trade' && item.pnl !== null && item.pnl !== undefined && (
                  <span className={`text-[10px] mono font-medium ${item.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                    {item.pnl >= 0 ? '+' : ''}${item.pnl.toFixed(2)}
                  </span>
                )}

                {/* Order type for pending */}
                {item.type === 'order' && (
                  <>
                    <span className="text-[9px] px-1 py-0.5 rounded bg-accent-blue/10 text-accent-blue uppercase">
                      {item.orderType}
                    </span>
                    <button
                      onClick={() => onCancelOrder(item.orderId)}
                      className="p-0.5 rounded hover:bg-accent-red/10 text-gray-600 hover:text-accent-red transition-colors"
                    >
                      <X size={10} />
                    </button>
                  </>
                )}

                {/* Status icon */}
                {item.type === 'trade' && (
                  <CheckCircle2 size={10} className="text-accent-green/40 flex-shrink-0" />
                )}

                {/* Time */}
                <span className="text-[9px] mono text-gray-700">{item.time}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
