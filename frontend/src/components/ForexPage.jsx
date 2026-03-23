import { useState, useEffect } from 'react'
import { DollarSign, TrendingUp, TrendingDown, ArrowUpDown, Activity } from 'lucide-react'
import * as api from '../api'

export default function ForexPage() {
  const [pairs, setPairs] = useState([])
  const [selectedPair, setSelectedPair] = useState(null)
  const [indicators, setIndicators] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let attempts = 0
    let timer = null

    const fetchData = async () => {
      try {
        const data = await api.getForexPairs()
        const arr = Array.isArray(data) ? data : []
        setPairs(arr)
        if (arr.length > 0) {
          setLoading(false)
          clearTimeout(timer)
          timer = setInterval(fetchData, 10000)
          return
        }
      } catch (e) {
        console.error('Forex fetch error:', e)
      }
      attempts++
      if (attempts > 15) setLoading(false)
    }

    fetchData()
    timer = setInterval(fetchData, 3000)
    return () => clearInterval(timer)
  }, [])

  const handleSelect = async (pair) => {
    setSelectedPair(pair)
    try {
      const res = await api.getForexIndicators(pair.id)
      setIndicators(res?.indicators || null)
    } catch (e) {
      console.error('Indicator fetch error:', e)
    }
  }

  const changeColor = (c) => (c || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'
  const borderGlow = (c) => (c || 0) >= 0
    ? 'border-accent-green/20 hover:border-accent-green/40'
    : 'border-accent-red/20 hover:border-accent-red/40'

  const safe = (v, digits = 5) => (v != null && !isNaN(v)) ? Number(v).toFixed(digits) : '—'

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <DollarSign size={24} className="text-accent-blue" />
          <h1 className="text-xl font-semibold text-gray-200">Forex</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass p-4 animate-pulse">
              <div className="h-5 bg-white/5 rounded w-1/2 mb-3" />
              <div className="h-8 bg-white/5 rounded w-2/3 mb-2" />
              <div className="h-4 bg-white/5 rounded w-1/3" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <DollarSign size={24} className="text-accent-blue" />
        <div>
          <h1 className="text-xl font-semibold text-gray-200">Forex</h1>
          <p className="text-xs text-gray-500">{pairs.length} major currency pairs · Real-time data</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pairs grid */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center gap-2 mb-2">
            <ArrowUpDown size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Currency Pairs</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {pairs.map((pair) => {
              const change = (pair.change || 0) * 100  // fraction → percent
              return (
                <button
                  key={pair.id}
                  onClick={() => handleSelect(pair)}
                  className={`glass p-4 text-left transition-all border ${borderGlow(change)} ${
                    selectedPair?.id === pair.id ? 'ring-1 ring-accent-blue' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-200">{pair.symbol || pair.id}</span>
                    {change >= 0
                      ? <TrendingUp size={14} className="text-accent-green" />
                      : <TrendingDown size={14} className="text-accent-red" />
                    }
                  </div>
                  <div className="text-xl font-semibold text-gray-100 tabular-nums mb-1">
                    {safe(pair.price, 5)}
                  </div>
                  <div className={`text-sm tabular-nums ${changeColor(change)}`}>
                    {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-600 mt-2 pt-2 border-t border-white/[0.04]">
                    <span>H: {safe(pair.high24h, 5)}</span>
                    <span>L: {safe(pair.low24h, 5)}</span>
                    <span>Vol: {pair.volume || '—'}</span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Heatmap */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Activity size={16} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-300">Performance Heatmap</span>
            </div>
            <div className="grid grid-cols-5 gap-2">
              {pairs.map((p) => {
                const pct = (p.change || 0) * 100
                const bg = pct >= 1 ? 'bg-green-600/80' : pct >= 0 ? 'bg-green-800/50' : pct >= -1 ? 'bg-red-800/50' : 'bg-red-600/80'
                return (
                  <div key={p.id} className={`${bg} rounded-lg p-3 text-center transition-all hover:scale-105 cursor-pointer`} onClick={() => handleSelect(p)}>
                    <div className="text-xs font-medium text-white">{p.symbol}</div>
                    <div className="text-[10px] text-white/80 mt-0.5">
                      {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        <div>
          {selectedPair ? (
            <div className="glass p-5 space-y-5 sticky top-24">
              <div>
                <h3 className="text-lg font-semibold text-gray-200">{selectedPair.symbol}</h3>
                <p className="text-xs text-gray-500">{selectedPair.name}</p>
              </div>
              <div className="text-3xl font-bold text-gray-100 tabular-nums">
                {safe(selectedPair.price, 5)}
              </div>
              <div className={`text-lg font-medium ${changeColor((selectedPair.change || 0) * 100)}`}>
                {(selectedPair.change || 0) * 100 >= 0 ? '+' : ''}{((selectedPair.change || 0) * 100).toFixed(2)}%
              </div>

              {/* Indicators */}
              {indicators && (
                <div className="space-y-3 border-t border-white/[0.04] pt-4">
                  <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">Technical Indicators</h4>

                  <IndicatorRow label="SMA (10)" value={safe(indicators.sma_10, 5)} />
                  <IndicatorRow label="SMA (20)" value={safe(indicators.sma_20, 5)} />
                  <IndicatorRow label="SMA (50)" value={safe(indicators.sma_50, 5)} />

                  <div className="glass p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500">RSI (14)</span>
                      <span className={`text-sm font-semibold tabular-nums ${
                        (indicators.rsi_14 || 50) < 30 ? 'text-accent-green' :
                        (indicators.rsi_14 || 50) > 70 ? 'text-accent-red' : 'text-gray-300'
                      }`}>
                        {safe(indicators.rsi_14, 2)}
                      </span>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-1.5">
                      <div
                        className={`h-full rounded-full ${
                          (indicators.rsi_14 || 50) < 30 ? 'bg-accent-green' :
                          (indicators.rsi_14 || 50) > 70 ? 'bg-accent-red' : 'bg-accent-blue'
                        }`}
                        style={{ width: `${Math.min(indicators.rsi_14 || 0, 100)}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-gray-600 mt-1">
                      {(indicators.rsi_14 || 50) < 30 ? 'Oversold' :
                       (indicators.rsi_14 || 50) > 70 ? 'Overbought' : 'Neutral'}
                    </div>
                  </div>

                  <IndicatorRow
                    label="MACD"
                    value={safe(indicators.macd, 5)}
                    color={(indicators.macd || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'}
                  />
                  <IndicatorRow label="MACD Signal" value={safe(indicators.macd_signal, 5)} />
                  <IndicatorRow label="BB Upper" value={safe(indicators.bb_upper, 5)} />
                  <IndicatorRow label="BB Lower" value={safe(indicators.bb_lower, 5)} />
                  <IndicatorRow label="ATR (14)" value={safe(indicators.atr_14, 5)} />
                </div>
              )}
            </div>
          ) : (
            <div className="glass p-5 text-center">
              <Activity size={24} className="mx-auto mb-2 text-gray-600" />
              <p className="text-sm text-gray-500">Select a pair for analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function IndicatorRow({ label, value, color = 'text-gray-300' }) {
  return (
    <div className="flex justify-between items-center py-1.5 px-3 rounded-lg bg-white/[0.02]">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-sm font-medium tabular-nums ${color}`}>{value}</span>
    </div>
  )
}
