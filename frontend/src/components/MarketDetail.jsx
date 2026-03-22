/**
 * MarketDetail — Center panel showing selected market info,
 * orderbook, and trade execution in Bloomberg terminal style.
 */

import { useState } from 'react'
import { TrendingUp, TrendingDown, ShoppingCart, Clock } from 'lucide-react'

const PLATFORM_LABELS = {
  polymarket: { buyLabel: 'Buy YES', sellLabel: 'Sell YES', sizeLabel: 'Shares' },
  binance: { buyLabel: 'Buy', sellLabel: 'Sell', sizeLabel: 'Amount' },
  hyperliquid: { buyLabel: 'Long', sellLabel: 'Short', sizeLabel: 'Size' },
}

export default function MarketDetail({ market, orderBook, onPlaceOrder, cash, positions }) {
  const [side, setSide] = useState('buy')
  const [orderType, setOrderType] = useState('market')
  const [size, setSize] = useState('')
  const [price, setPrice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!market) {
    return (
      <div className="flex flex-col h-full bg-[var(--term-panel)]">
        <div className="term-panel-header">
          <span>Market Detail</span>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
          Select a market from the scanner
        </div>
      </div>
    )
  }

  const pl = PLATFORM_LABELS[market.platform] || PLATFORM_LABELS.binance
  const isPrediction = market.marketType === 'prediction'
  const isPerp = market.marketType === 'perp'
  const decimals = isPrediction ? 4 : market.price > 100 ? 0 : 2
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

  return (
    <div className="flex flex-col h-full bg-[var(--term-panel)]">
      {/* Market info bar */}
      <div className="term-panel-header">
        <div className="flex items-center gap-2">
          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
            market.platform === 'polymarket' ? 'badge-pm' :
            market.platform === 'binance' ? 'badge-bn' : 'badge-hl'
          }`}>
            {market.platform === 'polymarket' ? 'PM' : market.platform === 'binance' ? 'BN' : 'HL'}
          </span>
          <span className="text-gray-300 normal-case text-xs font-medium tracking-normal">{market.name}</span>
          {market.dataSource === 'live' ? (
            <span className="badge-live text-[9px] font-bold px-1.5 py-0.5 rounded">LIVE</span>
          ) : (
            <span className="badge-sim text-[9px] font-bold px-1.5 py-0.5 rounded">SIM</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {market.symbol && <span className="text-gray-500 mono text-[10px]">{market.symbol}</span>}
          <span className="text-gray-500 text-[10px]">Vol: {market.volume}</span>
        </div>
      </div>

      {/* Price bar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.06]">
        <div className="flex items-baseline gap-3">
          <span className="text-2xl font-bold mono tabular-nums text-gray-100">
            ${market.price?.toFixed(decimals)}
          </span>
          <span className={`text-sm mono tabular-nums font-medium flex items-center gap-1 ${
            (market.change || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'
          }`}>
            {(market.change || 0) >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {(market.change || 0) >= 0 ? '+' : ''}{((market.change || 0) * 100).toFixed(2)}%
          </span>
          {isPrediction && (
            <span className="text-xs text-gray-500">
              YES: {market.yesPrice?.toFixed(2)} / NO: {market.noPrice?.toFixed(2)}
            </span>
          )}
          {isPerp && market.fundingRate !== undefined && (
            <span className={`text-xs ${(market.fundingRate || 0) >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              Funding: {((market.fundingRate || 0) * 100).toFixed(4)}%
            </span>
          )}
          {isPerp && market.leverageMax && (
            <span className="text-xs text-accent-cyan">Max {market.leverageMax}x</span>
          )}
        </div>
        {market.category && (
          <span className="text-[10px] text-gray-600 uppercase tracking-wider">{market.category}</span>
        )}
      </div>

      {/* Main content: Orderbook + Trade */}
      <div className="flex-1 flex overflow-hidden">
        {/* Orderbook — left half */}
        <div className="flex-1 flex flex-col border-r border-white/[0.06] overflow-hidden">
          <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-gray-600 font-medium border-b border-white/[0.06] flex justify-between">
            <span>Order Book</span>
            <span className="mono">{market.name?.slice(0, 30)}</span>
          </div>

          {/* Book header */}
          <div className="flex px-3 py-1 text-[9px] uppercase tracking-wider text-gray-600 border-b border-white/[0.04]">
            <span className="flex-1">Size</span>
            <span className="w-20 text-center">Bid</span>
            <span className="w-4" />
            <span className="w-20 text-center">Ask</span>
            <span className="flex-1 text-right">Size</span>
          </div>

          {/* Book rows */}
          <div className="flex-1 overflow-y-auto">
            {(orderBook?.bids?.length || orderBook?.asks?.length) ? (
              <>
                {Array.from({ length: Math.max(orderBook.bids?.length || 0, orderBook.asks?.length || 0, 8) }).map((_, i) => {
                  const bid = orderBook.bids?.[i]
                  const ask = orderBook.asks?.[i]
                  const maxSize = Math.max(
                    ...(orderBook.bids || []).map(b => b.size),
                    ...(orderBook.asks || []).map(a => a.size),
                    1
                  )
                  return (
                    <div key={i} className="flex items-center px-3 py-0.5 text-xs">
                      <div className="flex-1 relative">
                        {bid && (
                          <>
                            <div
                              className="absolute right-0 top-0 bottom-0 bg-accent-green/[0.06] rounded-l"
                              style={{ width: `${(bid.size / maxSize) * 100}%` }}
                            />
                            <span className="relative mono tabular-nums text-gray-400">{bid.size.toLocaleString()}</span>
                          </>
                        )}
                      </div>
                      <span className="w-20 text-center mono tabular-nums font-medium text-accent-green">
                        {bid ? bid.price.toFixed(isPrediction ? 3 : 2) : ''}
                      </span>
                      <span className="w-4 text-center text-gray-700">|</span>
                      <span className="w-20 text-center mono tabular-nums font-medium text-accent-red">
                        {ask ? ask.price.toFixed(isPrediction ? 3 : 2) : ''}
                      </span>
                      <div className="flex-1 relative text-right">
                        {ask && (
                          <>
                            <div
                              className="absolute left-0 top-0 bottom-0 bg-accent-red/[0.06] rounded-r"
                              style={{ width: `${(ask.size / maxSize) * 100}%` }}
                            />
                            <span className="relative mono tabular-nums text-gray-400">{ask.size.toLocaleString()}</span>
                          </>
                        )}
                      </div>
                    </div>
                  )
                })}
                {/* Spread */}
                {orderBook.bids?.[0] && orderBook.asks?.[0] && (
                  <div className="px-3 py-1 border-t border-white/[0.04] text-[10px] text-gray-600 flex justify-center gap-4 mono">
                    <span>Spread: ${(orderBook.asks[0].price - orderBook.bids[0].price).toFixed(isPrediction ? 3 : 2)}</span>
                    <span>Mid: ${((orderBook.asks[0].price + orderBook.bids[0].price) / 2).toFixed(isPrediction ? 4 : 3)}</span>
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-600 text-xs">
                No orderbook data
              </div>
            )}
          </div>
        </div>

        {/* Trade execution — right half */}
        <div className="w-[280px] flex flex-col overflow-hidden">
          <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-gray-600 font-medium border-b border-white/[0.06]">
            Trade Execution
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {/* Position banner */}
            {position && (
              <div className="p-2 rounded bg-white/[0.03] border border-white/[0.06] text-[11px]">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Position</span>
                  <span className={`font-medium mono ${position.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                    {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                  </span>
                </div>
                <div className="text-gray-400 mono mt-0.5">
                  {position.size} @ ${position.entryPrice.toFixed(decimals)}
                </div>
              </div>
            )}

            {/* Side toggle */}
            <div className="grid grid-cols-2 gap-1">
              <button
                onClick={() => setSide('buy')}
                className={`py-2 rounded text-xs font-semibold transition-all ${
                  side === 'buy'
                    ? 'bg-accent-green/20 text-accent-green border border-accent-green/30'
                    : 'bg-white/[0.03] text-gray-500 border border-white/[0.06]'
                }`}
              >
                {pl.buyLabel}
              </button>
              <button
                onClick={() => setSide('sell')}
                className={`py-2 rounded text-xs font-semibold transition-all ${
                  side === 'sell'
                    ? 'bg-accent-red/20 text-accent-red border border-accent-red/30'
                    : 'bg-white/[0.03] text-gray-500 border border-white/[0.06]'
                }`}
              >
                {pl.sellLabel}
              </button>
            </div>

            {/* Order type */}
            <div className="flex gap-1">
              {['market', 'limit'].map((t) => (
                <button
                  key={t}
                  onClick={() => setOrderType(t)}
                  className={`px-3 py-1 rounded text-[10px] font-medium uppercase transition-all ${
                    orderType === t
                      ? 'bg-accent-blue/15 text-accent-blue'
                      : 'text-gray-600 hover:text-gray-400'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Price input (limit only) */}
            {orderType === 'limit' && (
              <div>
                <label className="text-[10px] text-gray-600 uppercase tracking-wider mb-1 block">Price</label>
                <input
                  type="number"
                  step={isPrediction ? '0.01' : '0.01'}
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder={market.price?.toFixed(decimals)}
                  className="w-full px-2.5 py-2 bg-white/[0.03] border border-white/[0.06] rounded text-xs mono text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30"
                />
              </div>
            )}

            {/* Size input */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-[10px] text-gray-600 uppercase tracking-wider">{pl.sizeLabel}</label>
                {side === 'sell' && availableShares > 0 && (
                  <button
                    onClick={() => setSize(String(availableShares))}
                    className="text-[10px] text-accent-blue hover:underline"
                  >
                    MAX {availableShares}
                  </button>
                )}
              </div>
              <input
                type="number"
                step={isPrediction ? '1' : '0.001'}
                value={size}
                onChange={(e) => setSize(e.target.value)}
                placeholder={isPrediction ? '100' : '0.1'}
                className="w-full px-2.5 py-2 bg-white/[0.03] border border-white/[0.06] rounded text-xs mono text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/30"
              />
            </div>

            {/* Quick sizes */}
            <div className="flex gap-1">
              {side === 'buy' ? (
                isPrediction ? (
                  [50, 100, 250, 500].map((q) => (
                    <button key={q} onClick={() => setSize(String(q))}
                      className="flex-1 py-1 rounded bg-white/[0.03] text-[10px] text-gray-500 hover:bg-white/[0.06] mono">
                      {q}
                    </button>
                  ))
                ) : (
                  [100, 500, 1000, 2500].map((usd) => {
                    const qty = market.price ? (usd / market.price) : 0
                    return (
                      <button key={usd} onClick={() => setSize(qty.toFixed(4))}
                        className="flex-1 py-1 rounded bg-white/[0.03] text-[10px] text-gray-500 hover:bg-white/[0.06] mono">
                        ${usd >= 1000 ? `${usd/1000}K` : usd}
                      </button>
                    )
                  })
                )
              ) : (
                availableShares > 0 ? (
                  [25, 50, 75, 100].map((pct) => (
                    <button key={pct}
                      onClick={() => setSize(String(isPrediction ? Math.floor(availableShares * pct / 100) || 1 : +(availableShares * pct / 100).toFixed(4)))}
                      className="flex-1 py-1 rounded bg-white/[0.03] text-[10px] text-gray-500 hover:bg-white/[0.06] mono">
                      {pct}%
                    </button>
                  ))
                ) : (
                  <div className="text-[10px] text-gray-600 py-1">No position to sell</div>
                )
              )}
            </div>

            {/* Summary */}
            <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04] space-y-1 text-[11px] mono">
              <div className="flex justify-between">
                <span className="text-gray-600">Type</span>
                <span className="text-gray-400 uppercase">{orderType} {side}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">{side === 'buy' ? 'Est. Cost' : 'Est. Revenue'}</span>
                <span className="text-gray-300">${estimatedCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Available</span>
                <span className="text-gray-400">
                  {side === 'buy' ? `$${(cash || 0).toFixed(2)}` : `${availableShares} shares`}
                </span>
              </div>
              {side === 'buy' && estimatedCost > (cash || 0) && (
                <div className="text-accent-red text-[10px]">Insufficient funds</div>
              )}
            </div>

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={
                submitting || !size || parseFloat(size) <= 0 ||
                (side === 'buy' && estimatedCost > (cash || 0)) ||
                (side === 'sell' && (parseFloat(size) > availableShares || availableShares === 0))
              }
              className={`w-full py-2.5 rounded text-xs font-bold uppercase tracking-wider transition-all ${
                side === 'buy'
                  ? 'bg-accent-green/90 hover:bg-accent-green text-dark-900 disabled:bg-accent-green/20 disabled:text-gray-600'
                  : 'bg-accent-red/90 hover:bg-accent-red text-white disabled:bg-accent-red/20 disabled:text-gray-600'
              } disabled:cursor-not-allowed`}
            >
              {submitting ? 'Executing...' : `${side === 'buy' ? pl.buyLabel : pl.sellLabel} ${size || 0}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
