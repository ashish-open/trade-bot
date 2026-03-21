import { useState } from 'react'
import { ShoppingCart, TrendingUp, TrendingDown, Target, Coins, Zap } from 'lucide-react'

const PLATFORM_META = {
  polymarket: { icon: Target, label: 'Polymarket', color: 'text-accent-purple', buyLabel: 'Buy YES', sellLabel: 'Sell YES' },
  binance:    { icon: Coins,  label: 'Binance',    color: 'text-accent-yellow', buyLabel: 'Buy',     sellLabel: 'Sell' },
  hyperliquid:{ icon: Zap,    label: 'Hyperliquid', color: 'text-accent-cyan',  buyLabel: 'Long',    sellLabel: 'Short / Close' },
}

export default function TradePanel({ market, onPlaceOrder, cash, positions }) {
  const [side, setSide] = useState('buy')
  const [orderType, setOrderType] = useState('market')
  const [size, setSize] = useState('')
  const [price, setPrice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!market) {
    return (
      <div className="glass p-8 flex items-center justify-center text-gray-500">
        Select a market from the right panel to start trading
      </div>
    )
  }

  const pm = PLATFORM_META[market.platform] || PLATFORM_META.binance
  const PlatformIcon = pm.icon
  const isPrediction = market.marketType === 'prediction'
  const isPerp = market.marketType === 'perp'
  const decimals = isPrediction ? 4 : 2

  // Find current position for this market
  const position = (positions || []).find((p) => p.id === market.id)
  const availableShares = position ? position.size : 0

  const fillPrice = orderType === 'market' ? market.price : (parseFloat(price) || 0)
  const estimatedCost = (parseFloat(size) || 0) * fillPrice

  const handleSubmit = async () => {
    if (!size || parseFloat(size) <= 0) return
    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) return

    setSubmitting(true)
    await onPlaceOrder({
      market_id: market.id,
      side,
      order_type: orderType,
      size: parseFloat(size),
      price: orderType === 'limit' ? parseFloat(price) : null,
    })
    setSubmitting(false)
    setSize('')
    setPrice('')
  }

  const handleSellAll = () => {
    if (availableShares > 0) {
      setSide('sell')
      setSize(String(availableShares))
      setOrderType('market')
    }
  }

  return (
    <div className="glass p-5">
      {/* Market info header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <PlatformIcon size={14} className={pm.color} />
            <span className={`text-xs font-medium ${pm.color}`}>{pm.label}</span>
            {market.symbol && (
              <span className="text-xs text-gray-500">• {market.symbol}</span>
            )}
            {market.dataSource === 'live' ? (
              <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-glow" />
                LIVE
              </span>
            ) : (
              <span className="text-xs px-1.5 py-0.5 rounded bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/20">
                SIM
              </span>
            )}
          </div>
          <h3 className="text-sm font-medium text-gray-200">{market.name}</h3>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-2xl font-semibold tabular-nums text-gray-100">
              ${market.price?.toFixed(decimals)}
            </span>
            <span className={`text-sm tabular-nums flex items-center gap-0.5 ${
              (market.change || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'
            }`}>
              {(market.change || 0) >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {((market.change || 0) * 100).toFixed(2)}%
            </span>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>Vol: {market.volume}</div>
          <div>{market.category}</div>
          {isPerp && market.fundingRate !== undefined && (
            <div className={`mt-1 ${(market.fundingRate || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              Funding: {((market.fundingRate || 0) * 100).toFixed(4)}%
            </div>
          )}
          {isPerp && market.leverageMax && (
            <div className="text-accent-cyan">Up to {market.leverageMax}x</div>
          )}
        </div>
      </div>

      {/* Position banner */}
      {position && (
        <div className="mb-4 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-between">
          <div className="text-xs">
            <span className="text-gray-500">Your position:</span>{' '}
            <span className="text-gray-200 font-medium">{position.size} {isPrediction ? 'shares' : market.symbol?.split('/')[0] || 'units'}</span>
            <span className="text-gray-500 ml-2">@</span>{' '}
            <span className="text-gray-400 tabular-nums">${position.entryPrice.toFixed(decimals)}</span>
            <span className={`ml-3 font-medium tabular-nums ${position.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)} ({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%)
            </span>
          </div>
          <button
            onClick={handleSellAll}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-accent-red/10 text-accent-red hover:bg-accent-red/20 border border-accent-red/20 transition-all"
          >
            Close All
          </button>
        </div>
      )}

      {/* Buy / Sell toggle */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <button
          onClick={() => setSide('buy')}
          className={`py-2.5 rounded-xl text-sm font-medium transition-all ${
            side === 'buy'
              ? 'bg-accent-green/20 text-accent-green border border-accent-green/30'
              : 'bg-white/[0.03] text-gray-400 border border-white/[0.06] hover:bg-white/[0.05]'
          }`}
        >
          {pm.buyLabel}
        </button>
        <button
          onClick={() => setSide('sell')}
          className={`py-2.5 rounded-xl text-sm font-medium transition-all ${
            side === 'sell'
              ? 'bg-accent-red/20 text-accent-red border border-accent-red/30'
              : 'bg-white/[0.03] text-gray-400 border border-white/[0.06] hover:bg-white/[0.05]'
          }`}
        >
          {pm.sellLabel}
        </button>
      </div>

      {/* Order type */}
      <div className="flex gap-2 mb-4">
        {['market', 'limit'].map((type) => (
          <button
            key={type}
            onClick={() => setOrderType(type)}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors capitalize ${
              orderType === type
                ? 'bg-accent-blue/20 text-accent-blue'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Inputs */}
      <div className="space-y-3 mb-4">
        {orderType === 'limit' && (
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Price ($)</label>
            <input
              type="number"
              step={isPrediction ? '0.01' : '0.01'}
              min={isPrediction ? '0.01' : '0.01'}
              max={isPrediction ? '0.99' : undefined}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={market.price?.toFixed(decimals)}
              className="w-full px-3 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30 tabular-nums"
            />
          </div>
        )}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-gray-500">
              {isPrediction ? 'Shares' : `Amount (${market.symbol?.split('/')[0] || 'units'})`}
            </label>
            {side === 'sell' && availableShares > 0 && (
              <button
                onClick={() => setSize(String(availableShares))}
                className="text-xs text-accent-blue hover:text-accent-blue/80 transition-colors"
              >
                Max ({availableShares})
              </button>
            )}
          </div>
          <input
            type="number"
            step={isPrediction ? '1' : '0.001'}
            min={isPrediction ? '1' : '0.001'}
            max={side === 'sell' ? availableShares : undefined}
            value={size}
            onChange={(e) => setSize(e.target.value)}
            placeholder={isPrediction ? '100' : '0.1'}
            className="w-full px-3 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30 tabular-nums"
          />
        </div>

        {/* Quick size buttons */}
        <div className="flex gap-2">
          {side === 'buy' ? (
            isPrediction ? (
              [50, 100, 250, 500].map((qty) => (
                <button key={qty} onClick={() => setSize(String(qty))}
                  className="flex-1 text-xs py-1.5 rounded-lg bg-white/[0.03] text-gray-400 hover:bg-white/[0.06] transition-colors">
                  {qty}
                </button>
              ))
            ) : (
              // Dollar amounts for spot/perp
              [100, 500, 1000, 2000].map((usd) => {
                const qty = market.price ? (usd / market.price) : 0
                return (
                  <button key={usd} onClick={() => setSize(qty.toFixed(isPrediction ? 0 : 4))}
                    className="flex-1 text-xs py-1.5 rounded-lg bg-white/[0.03] text-gray-400 hover:bg-white/[0.06] transition-colors">
                    ${usd}
                  </button>
                )
              })
            )
          ) : (
            availableShares > 0 ? (
              [25, 50, 75, 100].map((pct) => (
                <button key={pct}
                  onClick={() => setSize(String(isPrediction ? Math.floor(availableShares * pct / 100) || 1 : parseFloat((availableShares * pct / 100).toFixed(4))))}
                  className="flex-1 text-xs py-1.5 rounded-lg bg-white/[0.03] text-gray-400 hover:bg-white/[0.06] transition-colors">
                  {pct}%
                </button>
              ))
            ) : (
              <div className="text-xs text-gray-600 py-1.5">No position to sell</div>
            )
          )}
        </div>
      </div>

      {/* Order summary */}
      <div className="glass-subtle p-3 mb-4 space-y-1.5 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Order type</span>
          <span className="text-gray-300 capitalize">{orderType} {side}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">{side === 'buy' ? 'Est. cost' : 'Est. revenue'}</span>
          <span className="text-gray-300 tabular-nums">${estimatedCost.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">{side === 'buy' ? 'Available cash' : 'Available to sell'}</span>
          <span className="text-gray-300 tabular-nums">
            {side === 'buy' ? `$${(cash || 0).toFixed(2)}` : availableShares}
          </span>
        </div>
        {side === 'buy' && estimatedCost > (cash || 0) && (
          <div className="text-accent-red">Insufficient funds</div>
        )}
        {side === 'sell' && parseFloat(size) > availableShares && (
          <div className="text-accent-red">Insufficient shares</div>
        )}
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={
          submitting ||
          !size ||
          parseFloat(size) <= 0 ||
          (side === 'buy' && estimatedCost > (cash || 0)) ||
          (side === 'sell' && (parseFloat(size) > availableShares || availableShares === 0))
        }
        className={`w-full py-3 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
          side === 'buy'
            ? 'bg-accent-green hover:bg-accent-green/90 text-dark-900 disabled:bg-accent-green/30 disabled:text-dark-900/50'
            : 'bg-accent-red hover:bg-accent-red/90 text-white disabled:bg-accent-red/30 disabled:text-white/50'
        } disabled:cursor-not-allowed`}
      >
        <ShoppingCart size={16} />
        {submitting ? 'Placing...' : `${side === 'buy' ? pm.buyLabel : 'Sell'} ${size || 0} ${isPrediction ? 'Shares' : market.symbol?.split('/')[0] || ''}`}
      </button>
    </div>
  )
}
