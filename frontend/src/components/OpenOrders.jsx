import { X, Clock } from 'lucide-react'

export default function OpenOrders({ orders, onCancel }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Open Orders</h3>
        <span className="text-xs text-gray-600">{orders.length} pending</span>
      </div>

      <div className="space-y-1">
        {orders.map((order) => (
          <div
            key={order.id}
            className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
          >
            {/* Side badge */}
            <div
              className={`px-2 py-1 rounded-lg text-xs font-medium uppercase ${
                order.side === 'buy'
                  ? 'bg-accent-green/10 text-accent-green'
                  : 'bg-accent-red/10 text-accent-red'
              }`}
            >
              {order.side}
            </div>

            {/* Market & details */}
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-200 truncate">{order.market}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="capitalize">{order.type}</span>
                <span className="text-gray-600">|</span>
                <span className="tabular-nums">{order.size} shares @ ${order.price.toFixed(4)}</span>
              </div>
            </div>

            {/* Time */}
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock size={10} />
              <span>{order.createdAt ? order.createdAt.slice(11, 19) : ''}</span>
            </div>

            {/* Cancel button */}
            <button
              onClick={() => onCancel(order.id)}
              className="p-1.5 rounded-lg hover:bg-accent-red/10 text-gray-500 hover:text-accent-red transition-colors"
              title="Cancel order"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
