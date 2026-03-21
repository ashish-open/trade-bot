/**
 * WebSocket hook — connects to the backend for real-time updates.
 * Receives market prices, portfolio state, and positions every second.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export default function useWebSocket(url = 'ws://localhost:8000/ws/updates') {
  const [data, setData] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          setData(parsed)
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        console.log('WebSocket disconnected, reconnecting in 3s...')
        reconnectTimeout.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch (e) {
      console.error('WS connection failed:', e)
      reconnectTimeout.current = setTimeout(connect, 3000)
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
    }
  }, [connect])

  return { data, connected }
}
