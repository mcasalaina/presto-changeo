/**
 * WebSocket client module for Presto-Change-O
 * Provides connection management with automatic reconnection logic
 */

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WebSocketMessage {
  type: string
  payload?: unknown
}

export interface WebSocketHandlers {
  onStateChange?: (state: ConnectionState) => void
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
}

const DEFAULT_URL = 'ws://localhost:8000/ws'
const MAX_RECONNECT_DELAY = 30000
const INITIAL_RECONNECT_DELAY = 1000

/**
 * Creates a WebSocket connection with automatic reconnection logic
 * Uses exponential backoff: 1s, 2s, 4s, 8s... up to 30s max
 *
 * @param url - WebSocket server URL (defaults to ws://localhost:8000/ws)
 * @param handlers - Event handlers for connection state changes and messages
 * @returns WebSocket instance
 */
export function connectWebSocket(
  url: string = DEFAULT_URL,
  handlers: WebSocketHandlers = {}
): WebSocket {
  let reconnectDelay = INITIAL_RECONNECT_DELAY
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let shouldReconnect = true

  const { onStateChange, onMessage, onError } = handlers

  const connect = (): WebSocket => {
    onStateChange?.('connecting')

    const ws = new WebSocket(url)

    ws.onopen = () => {
      reconnectDelay = INITIAL_RECONNECT_DELAY
      onStateChange?.('connected')
    }

    ws.onclose = () => {
      onStateChange?.('disconnected')

      if (shouldReconnect) {
        reconnectTimeout = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY)
          connect()
        }, reconnectDelay)
      }
    }

    ws.onerror = (event) => {
      onStateChange?.('error')
      onError?.(event)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage
        onMessage?.(message)
      } catch {
        // Handle non-JSON messages if needed
        console.warn('Received non-JSON message:', event.data)
      }
    }

    // Expose cleanup function on the WebSocket instance
    const originalClose = ws.close.bind(ws)
    ws.close = (code?: number, reason?: string) => {
      shouldReconnect = false
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      originalClose(code, reason)
    }

    return ws
  }

  return connect()
}

/**
 * Sends a JSON message through the WebSocket connection
 * Automatically stringifies the message object
 *
 * @param ws - Active WebSocket connection
 * @param message - Message object to send (will be JSON stringified)
 */
export function sendMessage(ws: WebSocket, message: WebSocketMessage): void {
  if (ws.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket is not open. Current state:', ws.readyState)
    return
  }

  ws.send(JSON.stringify(message))
}

/**
 * Creates a typed message helper for consistent message formats
 *
 * @param type - Message type identifier
 * @param payload - Optional message payload
 * @returns Formatted WebSocket message
 */
export function createMessage(type: string, payload?: unknown): WebSocketMessage {
  return { type, payload }
}
