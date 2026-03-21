import { useState } from 'react'
import { Shield, Wallet, Bell, Sliders, Target, Coins, Zap, Check, Lock } from 'lucide-react'

export default function SettingsPage() {
  const [tradingMode, setTradingMode] = useState('paper')
  const [startingBalance, setStartingBalance] = useState('10000')
  const [notifications, setNotifications] = useState({
    orderFilled: true,
    priceAlert: false,
    positionPnl: true,
  })

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h2 className="text-xl font-semibold text-gray-200">Settings</h2>
        <p className="text-sm text-gray-500 mt-1">Configure your trading bot and platform connections</p>
      </div>

      {/* Trading Mode */}
      <div className="glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={16} className="text-accent-blue" />
          <h3 className="text-sm font-medium text-gray-300">Trading Mode</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            onClick={() => setTradingMode('paper')}
            className={`p-4 rounded-xl border text-left transition-all ${
              tradingMode === 'paper'
                ? 'bg-accent-green/10 border-accent-green/30'
                : 'bg-white/[0.02] border-white/[0.06] hover:border-white/10'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-200">Paper Trading</span>
              {tradingMode === 'paper' && <Check size={14} className="text-accent-green" />}
            </div>
            <p className="text-xs text-gray-500">Simulated orders with no real money. Safe for testing strategies.</p>
          </button>
          <button
            disabled
            className="p-4 rounded-xl border bg-white/[0.01] border-white/[0.04] text-left opacity-50 cursor-not-allowed"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-400">Live Trading</span>
              <Lock size={14} className="text-gray-600" />
            </div>
            <p className="text-xs text-gray-600">Real orders with real funds. Connect API keys below to enable.</p>
          </button>
        </div>
      </div>

      {/* Paper Trading Config */}
      <div className="glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <Wallet size={16} className="text-accent-green" />
          <h3 className="text-sm font-medium text-gray-300">Paper Trading Balance</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <label className="text-xs text-gray-500 mb-1 block">Starting Balance (USD)</label>
            <input
              type="number"
              value={startingBalance}
              onChange={(e) => setStartingBalance(e.target.value)}
              className="w-full px-3 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-sm text-gray-200 focus:outline-none focus:border-accent-blue/30"
            />
          </div>
          <button className="mt-5 px-4 py-2.5 rounded-xl text-xs font-medium bg-accent-blue/10 text-accent-blue hover:bg-accent-blue/20 border border-accent-blue/20 transition-all">
            Reset Balance
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2">Changing this resets all positions and trade history.</p>
      </div>

      {/* Platform Connections */}
      <div className="glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <Sliders size={16} className="text-accent-purple" />
          <h3 className="text-sm font-medium text-gray-300">Platform Connections</h3>
        </div>
        <div className="space-y-3">
          <PlatformRow
            icon={Target}
            name="Polymarket"
            description="Prediction markets on Polygon"
            status="simulated"
            color="text-accent-purple"
          />
          <PlatformRow
            icon={Coins}
            name="Binance"
            description="Crypto spot trading"
            status="simulated"
            color="text-accent-yellow"
          />
          <PlatformRow
            icon={Zap}
            name="Hyperliquid"
            description="Perpetual contracts & DEX"
            status="simulated"
            color="text-accent-cyan"
          />
        </div>
      </div>

      {/* Notifications */}
      <div className="glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bell size={16} className="text-accent-yellow" />
          <h3 className="text-sm font-medium text-gray-300">Notifications</h3>
        </div>
        <div className="space-y-3">
          <ToggleRow
            label="Order Filled"
            description="Show toast when an order is executed"
            checked={notifications.orderFilled}
            onChange={(v) => setNotifications((p) => ({ ...p, orderFilled: v }))}
          />
          <ToggleRow
            label="Price Alerts"
            description="Notify when a market hits a target price"
            checked={notifications.priceAlert}
            onChange={(v) => setNotifications((p) => ({ ...p, priceAlert: v }))}
          />
          <ToggleRow
            label="Position P&L Threshold"
            description="Alert when unrealized P&L exceeds 10%"
            checked={notifications.positionPnl}
            onChange={(v) => setNotifications((p) => ({ ...p, positionPnl: v }))}
          />
        </div>
      </div>
    </div>
  )
}

function PlatformRow({ icon: Icon, name, description, status, color }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
      <Icon size={18} className={color} />
      <div className="flex-1">
        <div className="text-sm text-gray-200">{name}</div>
        <div className="text-xs text-gray-500">{description}</div>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs px-2 py-1 rounded-lg bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/20">
          {status}
        </span>
        <button className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.03] text-gray-400 hover:text-gray-200 hover:bg-white/[0.06] transition-colors border border-white/[0.06]">
          Connect API
        </button>
      </div>
    </div>
  )
}

function ToggleRow({ label, description, checked, onChange }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
      <div>
        <div className="text-sm text-gray-200">{label}</div>
        <div className="text-xs text-gray-500">{description}</div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-5 rounded-full transition-colors ${
          checked ? 'bg-accent-blue' : 'bg-white/10'
        }`}
      >
        <div
          className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  )
}
