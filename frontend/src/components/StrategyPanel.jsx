import { useState } from 'react'
import { Play, Pause, Settings, Zap, TrendingUp, TrendingDown, ChevronDown, ChevronUp, Activity, AlertCircle } from 'lucide-react'
import { updateStrategy, evaluateStrategies } from '../api'

export default function StrategyPanel({ strategies, onRefresh }) {
  const [expandedStrategy, setExpandedStrategy] = useState(null)
  const [evaluating, setEvaluating] = useState(false)

  const handleToggle = async (strategy) => {
    try {
      await updateStrategy(strategy.name, { enabled: !strategy.enabled })
      if (onRefresh) onRefresh()
    } catch (e) {
      console.error('Failed to toggle strategy:', e)
    }
  }

  const handleEvaluateNow = async () => {
    setEvaluating(true)
    try {
      const result = await evaluateStrategies()
      if (onRefresh) onRefresh()
    } catch (e) {
      console.error('Evaluation failed:', e)
    }
    setEvaluating(false)
  }

  // If strategies haven't loaded from the API yet, show placeholder
  if (!strategies || strategies.length === 0) {
    return (
      <div className="glass p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-400">Strategies</h3>
        </div>
        <div className="text-center py-6 text-gray-500 text-sm">
          <Activity size={20} className="mx-auto mb-2 opacity-50" />
          Loading strategies...
        </div>
      </div>
    )
  }

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">
          Strategies
          <span className="ml-2 text-xs text-accent-purple">
            {strategies.filter(s => s.enabled).length} active
          </span>
        </h3>
        <button
          onClick={handleEvaluateNow}
          disabled={evaluating}
          className="text-xs px-3 py-1.5 rounded-lg bg-accent-purple/10 text-accent-purple hover:bg-accent-purple/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          <Zap size={12} className={evaluating ? 'animate-spin' : ''} />
          {evaluating ? 'Running...' : 'Evaluate Now'}
        </button>
      </div>

      <div className="space-y-3">
        {strategies.map((strategy) => {
          const isActive = strategy.enabled
          const isExpanded = expandedStrategy === strategy.name
          const recentSignals = strategy.recentSignals || []
          const execCount = strategy.executionCount || 0

          return (
            <div
              key={strategy.name}
              className="glass-subtle overflow-hidden transition-colors"
            >
              <div className="p-4 hover:bg-white/[0.03]">
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
                      onClick={() => handleToggle(strategy)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-accent-red/10 text-accent-red hover:bg-accent-red/20'
                          : 'bg-accent-green/10 text-accent-green hover:bg-accent-green/20'
                      }`}
                      title={isActive ? 'Pause' : 'Resume'}
                    >
                      {isActive ? <Pause size={12} /> : <Play size={12} />}
                    </button>
                    <button
                      onClick={() => setExpandedStrategy(isExpanded ? null : strategy.name)}
                      className="p-1.5 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 transition-colors"
                    >
                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-xs text-gray-500 mb-0.5">Markets</div>
                    <div className="text-sm tabular-nums text-gray-300">
                      {(strategy.markets || []).length}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-0.5">Signals</div>
                    <div className="text-sm tabular-nums text-gray-300">
                      {recentSignals.length}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-0.5">Executed</div>
                    <div className="text-sm tabular-nums text-accent-cyan">
                      {execCount}
                    </div>
                  </div>
                </div>

                <div className="mt-2 text-xs text-gray-600">
                  {strategy.description}
                </div>
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="border-t border-white/5 p-4 bg-white/[0.01]">
                  {/* Parameters */}
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 mb-2 font-medium">Parameters</div>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(strategy.params || {}).map(([key, val]) => (
                        <div key={key} className="flex justify-between text-xs">
                          <span className="text-gray-500">{key.replace(/_/g, ' ')}</span>
                          <span className="text-gray-300 tabular-nums">{val}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Markets */}
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 mb-2 font-medium">Trading Markets</div>
                    <div className="flex flex-wrap gap-1.5">
                      {(strategy.markets || []).map(m => (
                        <span key={m} className="px-2 py-0.5 text-xs rounded bg-white/5 text-gray-400">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Max position */}
                  <div className="flex justify-between text-xs mb-3">
                    <span className="text-gray-500">Max Position Size</span>
                    <span className="text-gray-300">${strategy.maxPositionSize?.toFixed(0)}</span>
                  </div>

                  {/* Recent Signals */}
                  {recentSignals.length > 0 && (
                    <div>
                      <div className="text-xs text-gray-500 mb-2 font-medium">Recent Signals</div>
                      <div className="space-y-1.5">
                        {recentSignals.map((sig, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs">
                            {sig.side === 'buy' ? (
                              <TrendingUp size={10} className="text-accent-green" />
                            ) : (
                              <TrendingDown size={10} className="text-accent-red" />
                            )}
                            <span className={sig.side === 'buy' ? 'text-accent-green' : 'text-accent-red'}>
                              {sig.side.toUpperCase()}
                            </span>
                            <span className="text-gray-400 truncate flex-1">{sig.market}</span>
                            <span className="text-gray-600">
                              {sig.strength ? `${(sig.strength * 100).toFixed(0)}%` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
