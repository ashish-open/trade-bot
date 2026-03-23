/**
 * API client — all backend calls in one place.
 * Uses the Vite proxy (vite.config.js) to forward /api → localhost:8000
 */

const BASE = '/api'

async function fetchJSON(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ─── Platforms ──────────────────────────────────────────────────

export async function getPlatforms() {
  return fetchJSON('/platforms')
}

// ─── Portfolio ──────────────────────────────────────────────────

export async function getPortfolio() {
  return fetchJSON('/portfolio')
}

export async function getPositions() {
  return fetchJSON('/positions')
}

// ─── Markets ────────────────────────────────────────────────────

export async function getMarkets(platform = '', search = '', limit = 50) {
  const params = new URLSearchParams({ limit })
  if (platform) params.set('platform', platform)
  if (search) params.set('search', search)
  return fetchJSON(`/markets?${params}`)
}

export async function getOrderbook(marketId) {
  return fetchJSON(`/orderbook/${marketId}`)
}

// ─── Orders ─────────────────────────────────────────────────────

export async function placeOrder({ market_id, side, order_type, size, price }) {
  return fetchJSON('/orders', {
    method: 'POST',
    body: JSON.stringify({ market_id, side, order_type, size, price }),
  })
}

export async function getOpenOrders() {
  return fetchJSON('/orders')
}

export async function cancelOrder(orderId) {
  return fetchJSON(`/orders/${orderId}`, { method: 'DELETE' })
}

// ─── Trades ─────────────────────────────────────────────────────

export async function getTradeHistory(limit = 50) {
  return fetchJSON(`/trades?limit=${limit}`)
}

// ─── Strategies ────────────────────────────────────────────────

export async function getStrategies() {
  return fetchJSON('/strategies')
}

export async function getAvailableStrategies() {
  return fetchJSON('/strategies/available')
}

export async function registerStrategy({ key, markets, max_position_size, params, enabled }) {
  return fetchJSON('/strategies/register', {
    method: 'POST',
    body: JSON.stringify({ key, markets, max_position_size, params, enabled }),
  })
}

export async function updateStrategy(name, updates) {
  return fetchJSON(`/strategies/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

export async function deleteStrategy(name) {
  return fetchJSON(`/strategies/${encodeURIComponent(name)}`, { method: 'DELETE' })
}

export async function evaluateStrategies() {
  return fetchJSON('/strategies/evaluate', { method: 'POST' })
}

export async function getSignals(limit = 50) {
  return fetchJSON(`/strategies/signals?limit=${limit}`)
}

export async function getExecutions(limit = 50) {
  return fetchJSON(`/strategies/executions?limit=${limit}`)
}

export async function getStrategyStats() {
  return fetchJSON('/strategies/stats')
}

// ─── Indicators ────────────────────────────────────────────────

export async function getIndicators(marketId) {
  return fetchJSON(`/indicators/${marketId}`)
}

export async function getAllIndicators() {
  return fetchJSON('/indicators')
}

export async function getPriceHistory(marketId) {
  return fetchJSON(`/history/${marketId}`)
}

// ─── Equity ────────────────────────────────────────────────────

export async function getEquityMarkets(search = '', sector = '', type = '') {
  const params = new URLSearchParams({ limit: 50 })
  if (search) params.set('search', search)
  if (sector) params.set('sector', sector)
  if (type) params.set('type', type)
  return fetchJSON(`/equity/markets?${params}`)
}

export async function getEquityDetail(ticker) {
  return fetchJSON(`/equity/${ticker}`)
}

export async function getEquityHistory(ticker) {
  return fetchJSON(`/equity/${ticker}/history`)
}

export async function getEquityIndicators(ticker) {
  return fetchJSON(`/equity/${ticker}/indicators`)
}

export async function getEquityScreener(filters = {}) {
  const params = new URLSearchParams()
  if (filters.min_market_cap) params.set('min_market_cap', filters.min_market_cap)
  if (filters.max_pe) params.set('max_pe', filters.max_pe)
  if (filters.min_dividend_yield) params.set('min_dividend_yield', filters.min_dividend_yield)
  if (filters.sector) params.set('sector', filters.sector)
  return fetchJSON(`/equity/screener?${params}`)
}

export async function getEquitySectors() {
  return fetchJSON('/equity/sectors')
}

// ─── Forex ─────────────────────────────────────────────────────

export async function getForexPairs(search = '') {
  const params = new URLSearchParams({ limit: 50 })
  if (search) params.set('search', search)
  return fetchJSON(`/forex/pairs?${params}`)
}

export async function getForexDetail(pairId) {
  return fetchJSON(`/forex/${pairId}`)
}

export async function getForexHistory(pairId) {
  return fetchJSON(`/forex/${pairId}/history`)
}

export async function getForexIndicators(pairId) {
  return fetchJSON(`/forex/${pairId}/indicators`)
}

export async function getForexHeatmap() {
  return fetchJSON('/forex/heatmap')
}

// ─── Macro ─────────────────────────────────────────────────────

export async function getMacroOverview() {
  return fetchJSON('/macro/overview')
}

export async function getMacroIndices() {
  return fetchJSON('/macro/indices')
}

export async function getMacroTreasuries() {
  return fetchJSON('/macro/treasuries')
}

export async function getMacroCommodities() {
  return fetchJSON('/macro/commodities')
}

export async function getMacroFearGreed() {
  return fetchJSON('/macro/fear-greed')
}

export async function getMacroHistory(symbolId) {
  return fetchJSON(`/macro/${symbolId}/history`)
}

// ─── Health ─────────────────────────────────────────────────────

export async function getHealth() {
  return fetchJSON('/health')
}
