import { ArrowUpRight, ArrowDownRight, Clock, XCircle, CheckCircle2 } from 'lucide-react'

export default function TradeHistory({ trades }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Recent Trades</h3>
        <button className="text-xs text-accent-blue hover:text-accent-blue/80 transition-colors">
          View all
        </button>
      </div>

      <div className="space-y-1">
        {trades.length === 0 && (
          <div className="text-center text-gray-600 text-sm py-6">
            No trades yet — place your first order!
          </div>
        )}
        {trades.map((trade) => (
          <div
            key={trade.id}
            className="flex items-center gap-3 py-2 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
          >
            {/* Side indicator */}
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                trade.side === 'BUY'
                  ? 'bg-accent-green/10'
                  : 'bg-accent-red/10'
              }`}
            >
              {trade.side === 'BUY' ? (
                <ArrowUpRight size={14} className="text-accent-green" />
              ) : (
                <ArrowDownRight size={14} className="text-accent-red" />
              )}
            </div>

            {/* Market & details */}
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-200 truncate">{trade.market}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Clock size={10} />
                <span>{trade.time}</span>
                <span className="text-gray-600">|</span>
                <span>{trade.size} @ ${trade.price.toFixed(trade.price > 10 ? 2 : 4)}</span>
              </div>
            </div>

            {/* Status */}
            <div className="flex items-center gap-2">
              {trade.pnl !== null && (
                <span
                  className={`text-xs tabular-nums font-medium ${
                    trade.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'
                  }`}
                >
                  {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                </span>
              )}
              {trade.status === 'filled' ? (
                <CheckCircle2 size={14} className="text-accent-green/50" />
              ) : (
                <XCircle size={14} className="text-accent-red/50" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
