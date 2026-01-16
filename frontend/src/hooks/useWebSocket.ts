import { useState, useEffect, useRef, useCallback } from 'react'
import {
  connectWebSocket,
  sendMessage,
  createMessage,
  type ConnectionState,
  type WebSocketMessage,
} from '../lib/websocket'

const DEFAULT_URL = 'ws://localhost:8000/ws'

export interface UseWebSocketReturn {
  status: ConnectionState
  send: (message: object) => void
  lastMessage: WebSocketMessage | null
  connect: () => void
  disconnect: () => void
}

/**
 * React hook for WebSocket state management
 * Auto-connects on mount, disconnects on unmount
 * Uses websocket.ts utilities for connection handling with automatic reconnection
 *
 * @param url - WebSocket server URL (defaults to ws://localhost:8000/ws)
 * @returns Object with status, send function, lastMessage, connect, and disconnect
 */
export function useWebSocket(url: string = DEFAULT_URL): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const urlRef = useRef(url)

  // Update URL ref when it changes
  urlRef.current = url

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
      onMessage: setLastMessage,
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
    lastMessage,
    connect,
    disconnect,
  }
}
