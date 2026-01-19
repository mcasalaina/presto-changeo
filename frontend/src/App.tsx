import { useState, useEffect, useRef, useCallback } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { TypingIndicator } from './components/TypingIndicator'
import type { ConnectionState, WebSocketMessage } from './lib/websocket'
import './App.css'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function App() {
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. Say "Presto-Change-O, you\'re a bank" to transform this interface into any industry!',
      timestamp: new Date()
    }
  ])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isTyping, setIsTyping] = useState(false)
  const streamingIdRef = useRef<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Handle incoming WebSocket messages via callback (avoids state batching issues)
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'chat_start') {
      // AI is starting to respond - show typing indicator and create placeholder message
      setIsTyping(true)
      const newId = Date.now().toString()
      streamingIdRef.current = newId
      setMessages(prev => [...prev, {
        id: newId,
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }])
    } else if (message.type === 'chat_chunk') {
      const { text, done } = message.payload as { text: string; done: boolean }
      if (done) {
        // Streaming complete
        setIsTyping(false)
        streamingIdRef.current = null
      } else if (text && streamingIdRef.current) {
        // Append text to current streaming message
        const currentId = streamingIdRef.current
        setMessages(prev => prev.map(msg =>
          msg.id === currentId
            ? { ...msg, content: msg.content + text }
            : msg
        ))
      }
    } else if (message.type === 'chat_error') {
      // Handle error from backend
      setIsTyping(false)
      const { error } = message.payload as { error: string }
      if (streamingIdRef.current) {
        const currentId = streamingIdRef.current
        setMessages(prev => prev.map(msg =>
          msg.id === currentId
            ? { ...msg, content: `Error: ${error}` }
            : msg
        ))
        streamingIdRef.current = null
      }
    }
  }, [])

  const { status, send } = useWebSocket({ onMessage: handleMessage })

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const getStatusColor = (status: ConnectionState): string => {
    switch (status) {
      case 'connected': return '#22c55e'
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
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleNewChat = () => {
    // Clear frontend messages
    setMessages([{
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. Say "Presto-Change-O, you\'re a bank" to transform this interface into any industry!',
      timestamp: new Date()
    }])
    // Tell backend to clear history
    send({ type: 'clear_chat', payload: {} })
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'accounts', label: 'Accounts', icon: '👤' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'history', label: 'History', icon: '📋' },
    { id: 'settings', label: 'Settings', icon: '⚙️' }
  ]

  return (
    <div className="app">
      {/* Left Panel - Chat */}
      <aside className="chat-panel">
        <header className="chat-header">
          <span className="header-title">Chat Assistant</span>
          <div className="header-actions">
            <button className="new-chat-button" onClick={handleNewChat} title="New Chat">
              +
            </button>
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
          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
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
        <div className="visualization-area">
          <div className="viz-content">
            <div className="viz-icon">📊</div>
            <h2>Welcome</h2>
            <p>Say "Presto-Change-O, you're a bank" to transform this interface.</p>
            <p className="viz-hint">Charts and data will appear here based on your queries.</p>
          </div>
        </div>

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
