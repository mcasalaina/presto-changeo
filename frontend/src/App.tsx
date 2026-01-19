import { useState, useEffect, useRef, useCallback } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useVoice } from './hooks/useVoice'
import { TypingIndicator } from './components/TypingIndicator'
import { Dashboard } from './components/Dashboard'
import { ChartRenderer } from './components/ChartRenderer'
import { PersonaCard } from './components/PersonaCard'
import { VoiceToggle } from './components/VoiceToggle'
import { ModeProvider, useMode } from './context/ModeContext'
import type { Mode, Persona } from './types/mode'
import type { Metric } from './components/MetricsPanel'
import type { ConnectionState, WebSocketMessage } from './lib/websocket'
import { getMetricsFromPersona } from './lib/personaMetrics'
import './App.css'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function AppContent() {
  const { mode, setMode } = useMode()
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your Banking assistant. Say "Presto-Change-O, you\'re an insurance company" or "...you\'re a healthcare provider" to transform this interface!',
      timestamp: new Date()
    }
  ])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isTyping, setIsTyping] = useState(false)
  const [visualization, setVisualization] = useState<React.ReactNode>(null)
  const [dashboardMetrics, setDashboardMetrics] = useState<Metric[] | undefined>(mode.defaultMetrics)
  const [persona, setPersona] = useState<Persona>(null)
  const streamingIdRef = useRef<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Voice hook for voice mode integration
  const {
    isEnabled: voiceEnabled,
    isMuted: voiceMuted,
    isListening,
    isSpeaking,
    status: voiceStatus,
    enable: enableVoice,
    disable: disableVoice,
    toggleMute: toggleVoiceMute
  } = useVoice({
    onTranscript: (role, text) => {
      // Add transcript as chat message for display
      if (text.trim()) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role,
          content: text,
          timestamp: new Date()
        }])
      }
    },
    onToolResult: (tool, result) => {
      // Reuse existing tool result handling (chart rendering)
      if (tool === 'show_chart') {
        const chartResult = result as {
          chart_type: 'line' | 'bar' | 'pie' | 'area'
          title: string
          data: Array<{ label: string; value: number }>
        }
        setVisualization(
          <ChartRenderer
            chartType={chartResult.chart_type}
            title={chartResult.title}
            data={chartResult.data}
          />
        )
      } else if (tool === 'show_metrics') {
        const metricsResult = result as {
          metrics: Array<{ label: string; value: string | number; unit?: string }>
        }
        setDashboardMetrics(metricsResult.metrics)
      }
    },
    onError: (error) => {
      console.error('Voice error:', error)
    }
  })

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
        // Streaming complete - remove empty messages (when AI only used tools without text)
        const currentId = streamingIdRef.current
        if (currentId) {
          setMessages(prev => prev.filter(msg =>
            msg.id !== currentId || msg.content.trim() !== ''
          ))
        }
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
    } else if (message.type === 'tool_result') {
      // Handle visualization tool results
      const { tool, result } = message.payload as { tool: string; result: Record<string, unknown> }

      if (tool === 'show_chart') {
        const chartResult = result as {
          chart_type: 'line' | 'bar' | 'pie' | 'area'
          title: string
          data: Array<{ label: string; value: number }>
        }
        setVisualization(
          <ChartRenderer
            chartType={chartResult.chart_type}
            title={chartResult.title}
            data={chartResult.data}
          />
        )
      } else if (tool === 'show_metrics') {
        const metricsResult = result as {
          metrics: Array<{ label: string; value: string | number; unit?: string }>
        }
        setDashboardMetrics(metricsResult.metrics)
      }
    } else if (message.type === 'mode_switch') {
      // Handle mode switch from backend
      // Backend sends snake_case, transform to camelCase for frontend
      interface BackendModePayload {
        mode: {
          id: string
          name: string
          theme: {
            primary: string
            secondary: string
            background: string
            surface: string
            text: string
            text_muted: string
          }
          tabs: Array<{ id: string; label: string; icon: string }>
          defaultMetrics: Array<{ label: string; value: string | number; unit?: string }>
        }
        persona?: Persona
      }
      const payload = message.payload as BackendModePayload
      const newMode: Mode = {
        id: payload.mode.id,
        name: payload.mode.name,
        theme: {
          primary: payload.mode.theme.primary,
          secondary: payload.mode.theme.secondary,
          background: payload.mode.theme.background,
          surface: payload.mode.theme.surface,
          text: payload.mode.theme.text,
          textMuted: payload.mode.theme.text_muted,
        },
        tabs: payload.mode.tabs,
        systemPrompt: '',
        defaultMetrics: payload.mode.defaultMetrics,
      }
      setMode(newMode)
      // Clear visualization on mode switch
      setVisualization(null)
      // Update persona and derive metrics from persona data for consistency
      if (payload.persona) {
        setPersona(payload.persona)
        // Use persona-derived metrics so dashboard matches PersonaCard
        setDashboardMetrics(getMetricsFromPersona(payload.persona, newMode.id))
      } else {
        // Fallback to static defaults if no persona
        setDashboardMetrics(newMode.defaultMetrics)
      }
      // Clear messages and add welcome message (backend will send welcome text via chat_chunk)
      setMessages([])
    }
  }, [setMode])

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
    // Clear frontend messages with mode-specific welcome
    setMessages([{
      id: '1',
      role: 'assistant',
      content: `Hello! I'm your ${mode.name} assistant. Say "Presto-Change-O, you're a bank/insurance/healthcare" to transform this interface!`,
      timestamp: new Date()
    }])
    // Reset visualization and metrics to current mode defaults
    setVisualization(null)
    setDashboardMetrics(mode.defaultMetrics)
    // Tell backend to clear history
    send({ type: 'clear_chat', payload: {} })
  }

  return (
    <div className="app">
      {/* Left Panel - Chat */}
      <aside className="chat-panel">
        <header className="chat-header">
          <span className="header-title">Chat Assistant</span>
          <div className="header-actions">
            <VoiceToggle
              isEnabled={voiceEnabled}
              isMuted={voiceMuted}
              isListening={isListening}
              isSpeaking={isSpeaking}
              status={voiceStatus}
              onEnable={enableVoice}
              onDisable={disableVoice}
              onToggleMute={toggleVoiceMute}
            />
            <button className="new-chat-button" onClick={handleNewChat} title="New Chat">
              +
            </button>
            <span className="status-dot" style={{ backgroundColor: getStatusColor(status) }} />
          </div>
        </header>

        <div className="chat-messages">
          {messages.map(msg => {
            // Check if this is the currently streaming message with no content yet
            const isStreamingEmpty = isTyping && msg.id === streamingIdRef.current && msg.content === ''

            return (
              <div key={msg.id} className={`chat-message ${msg.role}`}>
                {msg.role === 'assistant' && <div className="message-avatar">🤖</div>}
                <div className="message-content">
                  {isStreamingEmpty ? <TypingIndicator /> : <p>{msg.content}</p>}
                </div>
              </div>
            )
          })}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            className="chat-input"
            placeholder={voiceEnabled ? "Voice mode active - speak to chat" : "Chat with me here..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={status !== 'connected' || voiceEnabled}
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
        {persona && (
          <div className="persona-header">
            <PersonaCard persona={persona} modeId={mode.id} />
          </div>
        )}
        <Dashboard
          metrics={dashboardMetrics}
          visualization={visualization}
        />

        <nav className="bottom-tabs">
          {mode.tabs.map(tab => (
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

function App() {
  return (
    <ModeProvider>
      <AppContent />
    </ModeProvider>
  )
}

export default App
