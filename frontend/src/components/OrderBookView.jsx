export default function OrderBookView({ orderBook }) {
  const maxSize = Math.max(
    ...orderBook.bids.map((b) => b.size),
    ...orderBook.asks.map((a) => a.size)
  )

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Order Book</h3>
        <span className="text-xs text-gray-600">BTC $150k by July</span>
      </div>

      {/* Header */}
      <div className="flex text-xs text-gray-500 uppercase tracking-wider mb-2 px-1">
        <span className="flex-1">Size</span>
        <span className="w-20 text-center">Price</span>
        <span className="flex-1 text-right">Size</span>
      </div>

      {/* Book rows */}
      <div className="space-y-0.5">
        {orderBook.bids.map((bid, i) => {
          const ask = orderBook.asks[i]
          const bidWidth = (bid.size / maxSize) * 100
          const askWidth = ask ? (ask.size / maxSize) * 100 : 0

          return (
            <div key={i} className="flex items-center text-xs h-7 relative">
              {/* Bid side (left) */}
              <div className="flex-1 relative flex items-center">
                <div
                  className="absolute right-0 h-full bg-accent-green/8 rounded-l"
                  style={{ width: `${bidWidth}%` }}
                />
                <span className="relative z-10 tabular-nums text-gray-400 pl-1">
                  {bid.size.toLocaleString()}
                </span>
              </div>

              {/* Bid price */}
              <span className="w-20 text-center tabular-nums font-medium text-accent-green">
                {bid.price.toFixed(2)}
              </span>

              {/* Spread line */}
              {i === 0 && (
                <div className="absolute left-1/2 -translate-x-1/2 w-px h-full bg-white/10" />
              )}

              {/* Ask price */}
              <span className="w-20 text-center tabular-nums font-medium text-accent-red">
                {ask ? ask.price.toFixed(2) : ''}
              </span>

              {/* Ask side (right) */}
              <div className="flex-1 relative flex items-center justify-end">
                {ask && (
                  <>
                    <div
                      className="absolute left-0 h-full bg-accent-red/8 rounded-r"
                      style={{ width: `${askWidth}%` }}
                    />
                    <span className="relative z-10 tabular-nums text-gray-400 pr-1">
                      {ask.size.toLocaleString()}
                    </span>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Spread info */}
      <div className="mt-3 pt-3 border-t border-white/5 flex justify-between text-xs text-gray-500">
        <span>Spread: ${(orderBook.asks[0].price - orderBook.bids[0].price).toFixed(2)}</span>
        <span>Mid: ${((orderBook.asks[0].price + orderBook.bids[0].price) / 2).toFixed(3)}</span>
      </div>
    </div>
  )
}
