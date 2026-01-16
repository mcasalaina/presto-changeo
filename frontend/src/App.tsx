import { useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import type { ConnectionState } from './lib/websocket'
import './App.css'

function App() {
  const { status, send, lastMessage } = useWebSocket()
  const [messageInput, setMessageInput] = useState('')

  const getStatusColor = (status: ConnectionState): string => {
    switch (status) {
      case 'connected':
        return '#4ade80'
      case 'connecting':
        return '#facc15'
      case 'error':
        return '#f87171'
      default:
        return '#94a3b8'
    }
  }

  const getStatusLabel = (status: ConnectionState): string => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'disconnected':
        return 'Disconnected'
      case 'error':
        return 'Error'
      default:
        return status
    }
  }

  const handleSendMessage = () => {
    if (messageInput.trim()) {
      send({ type: 'echo', payload: { text: messageInput } })
      setMessageInput('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage()
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Presto-Change-O</h1>
        <div className="connection-status">
          <span
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(status) }}
          />
          <span className="status-text">{getStatusLabel(status)}</span>
        </div>
      </header>
      <main className="app-main">
        <p className="app-description">
          Dynamic AI Dashboard - Ready to transform into any industry
        </p>

        <div className="test-panel">
          <h2 className="test-panel-title">WebSocket Test</h2>
          <div className="test-input-group">
            <input
              type="text"
              className="test-input"
              placeholder="Type a message to echo..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={status !== 'connected'}
            />
            <button
              className="test-button"
              onClick={handleSendMessage}
              disabled={status !== 'connected' || !messageInput.trim()}
            >
              Send
            </button>
          </div>
          {lastMessage && (
            <div className="test-response">
              <span className="test-response-label">Last message:</span>
              <code className="test-response-content">
                {JSON.stringify(lastMessage, null, 2)}
              </code>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
