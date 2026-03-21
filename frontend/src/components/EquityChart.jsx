import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-subtle px-3 py-2 text-sm">
      <p className="text-gray-400 text-xs">{label}</p>
      <p className="text-accent-cyan font-semibold tabular-nums">
        ${payload[0].value.toLocaleString()}
      </p>
    </div>
  )
}

export default function EquityChart({ data }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Equity Curve</h3>
        <div className="flex gap-2">
          {['7D', '30D', '90D', 'ALL'].map((period) => (
            <button
              key={period}
              className={`text-xs px-2.5 py-1 rounded-lg transition-colors ${
                period === '30D'
                  ? 'bg-accent-blue/20 text-accent-blue'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#448aff" stopOpacity={0.3} />
                <stop offset="50%" stopColor="#7c4dff" stopOpacity={0.1} />
                <stop offset="100%" stopColor="#18ffff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#555', fontSize: 11 }}
              interval="preserveStartEnd"
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#555', fontSize: 11 }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
              domain={['dataMin - 200', 'dataMax + 200']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="url(#lineGradient)"
              strokeWidth={2}
              fill="url(#equityGradient)"
            />
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#448aff" />
                <stop offset="50%" stopColor="#7c4dff" />
                <stop offset="100%" stopColor="#18ffff" />
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
