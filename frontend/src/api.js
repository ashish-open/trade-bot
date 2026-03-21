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

// ─── Health ─────────────────────────────────────────────────────

export async function getHealth() {
  return fetchJSON('/health')
}
