import { Play, Pause, Settings, Zap, TrendingUp } from 'lucide-react'

export default function StrategyPanel({ strategies }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Strategies</h3>
        <button className="text-xs px-3 py-1.5 rounded-lg bg-accent-purple/10 text-accent-purple hover:bg-accent-purple/20 transition-colors flex items-center gap-1.5">
          <Zap size={12} />
          New Strategy
        </button>
      </div>

      <div className="space-y-3">
        {strategies.map((strategy) => {
          const isActive = strategy.status === 'active'
          return (
            <div
              key={strategy.id}
              className="glass-subtle p-4 hover:bg-white/[0.03] transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isActive ? 'bg-accent-green animate-pulse-glow' : 'bg-gray-600'
                    }`}
                  />
                  <span className="text-sm font-medium text-gray-200">
                    {strategy.name}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    className={`p-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-accent-red/10 text-accent-red hover:bg-accent-red/20'
                        : 'bg-accent-green/10 text-accent-green hover:bg-accent-green/20'
                    }`}
                    title={isActive ? 'Pause' : 'Resume'}
                  >
                    {isActive ? <Pause size={12} /> : <Play size={12} />}
                  </button>
                  <button className="p-1.5 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 transition-colors">
                    <Settings size={12} />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-gray-500 mb-0.5">Win Rate</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          strategy.winRate >= 60
                            ? 'bg-accent-green'
                            : strategy.winRate >= 50
                            ? 'bg-accent-yellow'
                            : 'bg-accent-red'
                        }`}
                        style={{ width: `${strategy.winRate}%` }}
                      />
                    </div>
                    <span className="text-xs tabular-nums text-gray-300">
                      {strategy.winRate}%
                    </span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-0.5">Trades</div>
                  <div className="text-sm tabular-nums text-gray-300">{strategy.trades}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-0.5">P&L</div>
                  <div
                    className={`text-sm tabular-nums font-medium ${
                      strategy.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'
                    }`}
                  >
                    {strategy.pnl >= 0 ? '+' : ''}${strategy.pnl.toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-600">{strategy.platform}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
