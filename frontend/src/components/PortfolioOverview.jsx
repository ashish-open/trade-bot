import { TrendingUp, TrendingDown, Activity, Target, BarChart3, Wallet } from 'lucide-react'

function StatCard({ label, value, subValue, icon: Icon, color = 'blue', glow = false }) {
  const colorMap = {
    green: 'text-accent-green',
    red: 'text-accent-red',
    blue: 'text-accent-blue',
    purple: 'text-accent-purple',
    cyan: 'text-accent-cyan',
    yellow: 'text-accent-yellow',
  }

  const glowMap = {
    green: 'glow-green',
    red: 'glow-red',
    blue: 'glow-blue',
    purple: 'glow-purple',
  }

  return (
    <div className={`glass p-5 ${glow ? glowMap[color] || '' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wider text-gray-500">{label}</span>
        <Icon size={16} className={colorMap[color]} />
      </div>
      <div className={`text-2xl font-semibold tabular-nums ${colorMap[color]}`}>
        {value}
      </div>
      {subValue && (
        <div className="text-xs text-gray-500 mt-1">{subValue}</div>
      )}
    </div>
  )
}

export default function PortfolioOverview({ stats }) {
  const pnlColor = stats.totalPnl >= 0 ? 'green' : 'red'
  const dayColor = stats.dayPnl >= 0 ? 'green' : 'red'

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Portfolio Value"
        value={`$${stats.totalValue.toLocaleString()}`}
        subValue={`${stats.openPositions} open positions`}
        icon={Wallet}
        color="blue"
        glow
      />
      <StatCard
        label="Total P&L"
        value={`${stats.totalPnl >= 0 ? '+' : ''}$${stats.totalPnl.toLocaleString()}`}
        subValue={`${stats.totalPnlPercent >= 0 ? '+' : ''}${stats.totalPnlPercent}% all time`}
        icon={stats.totalPnl >= 0 ? TrendingUp : TrendingDown}
        color={pnlColor}
        glow
      />
      <StatCard
        label="Today's P&L"
        value={`${stats.dayPnl >= 0 ? '+' : ''}$${stats.dayPnl.toLocaleString()}`}
        subValue={`${stats.dayPnlPercent >= 0 ? '+' : ''}${stats.dayPnlPercent}%`}
        icon={Activity}
        color={dayColor}
      />
      <StatCard
        label="Win Rate"
        value={`${stats.winRate}%`}
        subValue={`${stats.totalTrades} trades | ${stats.activeStrategies} strategies`}
        icon={Target}
        color="purple"
      />
    </div>
  )
}
