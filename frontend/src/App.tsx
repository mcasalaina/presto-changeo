import { useState } from 'react'
import './App.css'

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

function App() {
  const [connectionStatus] = useState<ConnectionStatus>('disconnected')

  const getStatusColor = (status: ConnectionStatus): string => {
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

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Presto-Change-O</h1>
        <div className="connection-status">
          <span
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(connectionStatus) }}
          />
          <span className="status-text">{connectionStatus}</span>
        </div>
      </header>
      <main className="app-main">
        <p className="app-description">
          Dynamic AI Dashboard - Ready to transform into any industry
        </p>
      </main>
    </div>
  )
}

export default App
