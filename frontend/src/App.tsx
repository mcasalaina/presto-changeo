import { useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import type { ConnectionState } from './lib/websocket'
import './App.css'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function App() {
  const { status, send } = useWebSocket()
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m Presto-Change-O, your dynamic AI dashboard. Say "Presto-Change-O, you\'re a bank" to transform me into any industry!',
      timestamp: new Date()
    }
  ])
  const [activeTab, setActiveTab] = useState('dashboard')

  const getStatusColor = (status: ConnectionState): string => {
    switch (status) {
      case 'connected': return '#4ade80'
      case 'connecting': return '#facc15'
      case 'error': return '#f87171'
      default: return '#94a3b8'
    }
  }

  const handleSendMessage = () => {
    if (!inputValue.trim() || status !== 'connected') return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    send({ type: 'chat', payload: { text: inputValue } })
    setInputValue('')

    // Placeholder response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I received your message. Chat functionality will be fully implemented in Phase 2.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    }, 500)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'accounts', label: 'Accounts', icon: '👤' },
    { id: 'history', label: 'History', icon: '📋' },
    { id: 'settings', label: 'Settings', icon: '⚙️' }
  ]

  return (
    <div className="app">
      {/* Left Panel - Chat */}
      <aside className="chat-panel">
        <header className="chat-header">
          <span className="header-title">Chat Assistant</span>
          <div className="connection-badge" style={{ backgroundColor: status === 'connected' ? '#065f46' : '#7c2d12' }}>
            <span className="status-dot" style={{ backgroundColor: getStatusColor(status) }} />
          </div>
        </header>

        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`chat-message ${msg.role}`}>
              {msg.role === 'assistant' && <div className="message-avatar">🤖</div>}
              <div className="message-content">
                <p>{msg.content}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            className="chat-input"
            placeholder="Chat with me here..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={status !== 'connected'}
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={status !== 'connected' || !inputValue.trim()}
          >
            ➤
          </button>
        </div>

        <p className="chat-disclaimer">
          AI can make mistakes. Consider checking important information.
        </p>
      </aside>

      {/* Right Panel - Dashboard */}
      <main className="dashboard-panel">
        {/* Central Visualization Area */}
        <div className="visualization-area">
          <div className="viz-placeholder">
            <div className="viz-icon">📊</div>
            <h3>Welcome</h3>
            <p>Say "Presto-Change-O, you're a bank" to transform this interface.</p>
            <p className="viz-hint">Charts and data will appear here based on your queries.</p>
          </div>
        </div>

        {/* Bottom Navigation Tabs */}
        <nav className="bottom-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </nav>
      </main>
    </div>
  )
}

export default App
