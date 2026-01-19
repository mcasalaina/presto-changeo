import { useState, useEffect, useRef, useCallback } from 'react'
import {
  connectWebSocket,
  sendMessage,
  createMessage,
  type ConnectionState,
  type WebSocketMessage,
} from '../lib/websocket'

const DEFAULT_URL = 'ws://localhost:8000/ws'

export interface UseWebSocketOptions {
  url?: string
  onMessage?: (message: WebSocketMessage) => void
}

export interface UseWebSocketReturn {
  status: ConnectionState
  send: (message: object) => void
  connect: () => void
  disconnect: () => void
}

/**
 * React hook for WebSocket state management
 * Auto-connects on mount, disconnects on unmount
 * Uses websocket.ts utilities for connection handling with automatic reconnection
 *
 * @param options - Configuration options including URL and message handler
 * @returns Object with status, send function, connect, and disconnect
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { url = DEFAULT_URL, onMessage } = options
  const [status, setStatus] = useState<ConnectionState>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const urlRef = useRef(url)
  const onMessageRef = useRef(onMessage)

  // Update refs when they change
  urlRef.current = url
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    // Don't create new connection if one exists and is open/connecting
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    wsRef.current = connectWebSocket(urlRef.current, {
      onStateChange: setStatus,
      onMessage: (msg) => onMessageRef.current?.(msg),
      onError: (error) => {
        console.error('WebSocket error:', error)
      },
    })
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((message: object) => {
    if (wsRef.current) {
      // If message has type and payload, send as-is, otherwise wrap it
      const wsMessage =
        'type' in message && typeof (message as Record<string, unknown>).type === 'string'
          ? (message as WebSocketMessage)
          : createMessage('message', message)
      sendMessage(wsRef.current, wsMessage)
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  }, [])

  // Auto-connect on mount, disconnect on unmount
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    status,
    send,
    connect,
    disconnect,
  }
}
