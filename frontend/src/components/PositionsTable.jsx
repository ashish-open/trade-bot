import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

export default function PositionsTable({ positions }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Open Positions</h3>
        <span className="text-xs text-gray-600">{positions.length} active</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-white/5">
              <th className="text-left pb-3 pr-4">Market</th>
              <th className="text-left pb-3 pr-4">Platform</th>
              <th className="text-center pb-3 pr-4">Side</th>
              <th className="text-right pb-3 pr-4">Size</th>
              <th className="text-right pb-3 pr-4">Entry</th>
              <th className="text-right pb-3 pr-4">Current</th>
              <th className="text-right pb-3">P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos) => {
              const isProfit = pos.pnl >= 0
              return (
                <tr
                  key={pos.id}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-3 pr-4">
                    <div className="max-w-[200px] truncate font-medium text-gray-200">
                      {pos.market}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400">
                      {pos.platform}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-center">
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        pos.side === 'YES' || pos.side === 'LONG'
                          ? 'bg-accent-green/10 text-accent-green'
                          : 'bg-accent-red/10 text-accent-red'
                      }`}
                    >
                      {pos.side}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-gray-300">
                    {pos.size.toLocaleString()}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-gray-400">
                    ${pos.entryPrice.toFixed(pos.entryPrice > 10 ? 2 : 4)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-gray-300">
                    ${pos.currentPrice.toFixed(pos.currentPrice > 10 ? 2 : 4)}
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {isProfit ? (
                        <ArrowUpRight size={14} className="text-accent-green" />
                      ) : (
                        <ArrowDownRight size={14} className="text-accent-red" />
                      )}
                      <span
                        className={`tabular-nums font-medium ${
                          isProfit ? 'text-accent-green' : 'text-accent-red'
                        }`}
                      >
                        {isProfit ? '+' : ''}${pos.pnl.toFixed(2)}
                      </span>
                      <span className={`text-xs ${isProfit ? 'text-accent-green/60' : 'text-accent-red/60'}`}>
                        ({isProfit ? '+' : ''}{pos.pnlPercent.toFixed(1)}%)
                      </span>
                    </div>
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
