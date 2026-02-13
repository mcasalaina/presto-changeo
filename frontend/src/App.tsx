import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useVoice } from './hooks/useVoice'
import { TypingIndicator } from './components/TypingIndicator'
import { Dashboard } from './components/Dashboard'
import { ChartRenderer } from './components/ChartRenderer'
import { VoiceToggle } from './components/VoiceToggle'
import { SettingsPanel } from './components/SettingsPanel'
import { ModeProvider, useMode } from './context/ModeContext'
import type { Mode, Persona } from './types/mode'
import type { Metric } from './components/MetricsPanel'
import type { WebSocketMessage } from './lib/websocket'
import { getMetricsFromPersona } from './lib/personaMetrics'
import './App.css'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function AppContent() {
  const { mode, setMode, persona: contextPersona, isLoading } = useMode()
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [initialMessageSet, setInitialMessageSet] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isTyping, setIsTyping] = useState(false)
  const [modeGenerating, setModeGenerating] = useState<string | null>(null)
  const [visualization, setVisualization] = useState<React.ReactNode>(null)
  const [dashboardMetrics, setDashboardMetrics] = useState<Metric[] | undefined>(undefined)
  const [persona, setPersona] = useState<Persona>(null)
  const [tabContentCache, setTabContentCache] = useState<Record<string, ReactNode>>({})
  const [tabLoading, setTabLoading] = useState(false)

  // Sync persona from context when restored from backend
  useEffect(() => {
    if (contextPersona && !persona) {
      setPersona(contextPersona)
      setDashboardMetrics(getMetricsFromPersona(contextPersona, mode.id))
    }
  }, [contextPersona, persona, mode.id])

  // Set default metrics when mode changes but no persona yet
  useEffect(() => {
    if (!persona && !contextPersona && !isLoading) {
      setDashboardMetrics(mode.defaultMetrics)
    }
  }, [mode, persona, contextPersona, isLoading])

  // Update browser tab title when company name changes
  useEffect(() => {
    document.title = mode.companyName
  }, [mode.companyName])

  // Set initial welcome message after state is loaded
  useEffect(() => {
    if (!isLoading && !initialMessageSet) {
      setMessages([{
        id: '1',
        role: 'assistant',
        content: `Hello! I'm your assistant at ${mode.companyName}. How can I help you today?`,
        timestamp: new Date()
      }])
      setInitialMessageSet(true)
    }
  }, [isLoading, initialMessageSet, mode.companyName])
  const streamingIdRef = useRef<string | null>(null)
  const voiceUserIdRef = useRef<string | null>(null)
  const voiceAssistantIdRef = useRef<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  // Block all incoming messages during mode switch to prevent old content leaking through
  const isSwitchingModeRef = useRef(false)

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
      // Block all transcripts during mode switch to prevent old content leaking
      if (isSwitchingModeRef.current) return

      // Accumulate transcript deltas into a single message per role
      // Track user and assistant separately so they don't interrupt each other
      if (!text) return

      const idRef = role === 'user' ? voiceUserIdRef : voiceAssistantIdRef

      // If no current message for this role, create the ID BEFORE setMessages
      // This prevents race conditions where multiple deltas arrive before callback runs
      if (!idRef.current) {
        idRef.current = Date.now().toString()
      }
      const messageId = idRef.current

      setMessages(prev => {
        const existingMsg = prev.find(m => m.id === messageId)

        if (existingMsg) {
          // Update existing message - replace placeholder or append
          return prev.map(msg => {
            if (msg.id !== messageId) return msg
            const newContent = msg.content === '...' ? text : msg.content + text
            return { ...msg, content: newContent }
          })
        }

        // Create new message with the pre-assigned ID
        return [...prev, {
          id: messageId,
          role,
          content: text,
          timestamp: new Date()
        }]
      })
    },
    onToolResult: (tool, result) => {
      if (tool === '_generating') {
        // Show loading spinner while background visualization generates
        const { vis_type } = result as { vis_type: string; description: string }
        setVisualization(
          <div className="visualization-loading">
            <div className="visualization-loading-spinner"></div>
            <p>Generating {vis_type === 'metrics' ? 'metrics' : 'chart'}...</p>
          </div>
        )
      } else if (tool === 'show_chart') {
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
    },
    onModeSwitch: (payload) => {
      // Handle mode switch from voice - same logic as chat WebSocket handler
      interface BackendModePayload {
        mode: {
          id: string
          name: string
          company_name: string
          tagline: string
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
          background_image?: string | null
          hero_image?: string | null
          chat_image?: string | null
        }
        persona?: Persona
      }
      const modePayload = payload as unknown as BackendModePayload
      const newMode: Mode = {
        id: modePayload.mode.id,
        name: modePayload.mode.name,
        companyName: modePayload.mode.company_name,
        tagline: modePayload.mode.tagline,
        theme: {
          primary: modePayload.mode.theme.primary,
          secondary: modePayload.mode.theme.secondary,
          background: modePayload.mode.theme.background,
          surface: modePayload.mode.theme.surface,
          text: modePayload.mode.theme.text,
          textMuted: modePayload.mode.theme.text_muted,
        },
        tabs: modePayload.mode.tabs,
        systemPrompt: '',
        defaultMetrics: modePayload.mode.defaultMetrics,
        backgroundImage: modePayload.mode.background_image ?? undefined,
        heroImage: modePayload.mode.hero_image ?? undefined,
        chatImage: modePayload.mode.chat_image ?? undefined,
      }
      // Keep blocking - old transcript chunks may still arrive after mode_switch
      // We'll unblock after a delay to let them drain
      streamingIdRef.current = null
      voiceUserIdRef.current = null
      voiceAssistantIdRef.current = null
      setIsTyping(false)

      setMode(newMode)
      setVisualization(null)
      setModeGenerating(null)  // Clear loading indicator
      setTabContentCache({})
      setActiveTab('dashboard')

      // Set up dashboard like New Conversation: use mode's default metrics
      setDashboardMetrics(newMode.defaultMetrics)
      if (modePayload.persona) {
        setPersona(modePayload.persona)
      }

      // Set welcome message like New Conversation does
      setMessages([{
        id: '1',
        role: 'assistant',
        content: `Hello! I'm your assistant at ${newMode.companyName}. How can I help you today?`,
        timestamp: new Date()
      }])

      // Keep blocking for 1 second to let any in-flight old messages drain
      // Only then allow new messages through
      setTimeout(() => {
        isSwitchingModeRef.current = false
      }, 1000)
    },
    onModeGenerating: (industry) => {
      if (industry) {
        // Mode switch starting - block all incoming messages immediately
        isSwitchingModeRef.current = true
        streamingIdRef.current = null
        voiceUserIdRef.current = null
        voiceAssistantIdRef.current = null
        setIsTyping(false)
        setMessages([])  // Clear immediately so old content can't leak through
        setModeGenerating(industry)
      } else {
        // Empty string means cancel (false positive)
        isSwitchingModeRef.current = false
        setModeGenerating(null)
      }
    },
    onInterrupt: () => {
      // User started speaking - reset assistant message ID so next response is new
      voiceAssistantIdRef.current = null
    },
    onUserSpeechEnd: () => {
      // Don't reset ref here - transcript arrives AFTER speech ends
      // The transcript handler will fill in the placeholder
    },
    onUserSpeechStart: () => {
      // Block during mode switch
      if (isSwitchingModeRef.current) return

      // Clean up any stale placeholder from previous speech that never got a transcript
      const oldId = voiceUserIdRef.current
      if (oldId) {
        setMessages(prev => prev.filter(msg =>
          msg.id !== oldId || msg.content !== '...'
        ))
      }
      // Create placeholder for user message to ensure correct ordering
      const newId = Date.now().toString()
      voiceUserIdRef.current = newId
      setMessages(prev => [...prev, {
        id: newId,
        role: 'user',
        content: '...',  // Placeholder, will be replaced by transcript
        timestamp: new Date()
      }])
    }
  })

  // Handle incoming WebSocket messages via callback (avoids state batching issues)
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'chat_start') {
      // Block during mode switch to prevent old content leaking
      if (isSwitchingModeRef.current) return

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
      // Block during mode switch to prevent old content leaking
      if (isSwitchingModeRef.current) return

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
        setActiveTab('dashboard')
      } else if (tool === 'show_metrics') {
        const metricsResult = result as {
          metrics: Array<{ label: string; value: string | number; unit?: string }>
        }
        setDashboardMetrics(metricsResult.metrics)
        setActiveTab('dashboard')
      }
    } else if (message.type === 'mode_generating') {
      // Mode switch starting - block all incoming messages immediately
      const payload = message.payload as { industry: string }
      isSwitchingModeRef.current = true
      streamingIdRef.current = null
      voiceUserIdRef.current = null
      voiceAssistantIdRef.current = null
      setIsTyping(false)
      setMessages([])  // Clear immediately so old content can't leak through
      setModeGenerating(payload.industry)
    } else if (message.type === 'mode_generating_cancel') {
      // Cancel mode generating indicator (false positive detection)
      isSwitchingModeRef.current = false
      setModeGenerating(null)
    } else if (message.type === 'mode_switch') {
      // Keep blocking - old chunks may still arrive after mode_switch
      streamingIdRef.current = null
      voiceUserIdRef.current = null
      voiceAssistantIdRef.current = null
      setIsTyping(false)

      // Clear the generating state
      setModeGenerating(null)
      // Handle mode switch from backend
      // Backend sends snake_case, transform to camelCase for frontend
      interface BackendModePayload {
        mode: {
          id: string
          name: string
          company_name: string
          tagline: string
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
          background_image?: string | null
          hero_image?: string | null
          chat_image?: string | null
        }
        persona?: Persona
      }
      const payload = message.payload as BackendModePayload
      const newMode: Mode = {
        id: payload.mode.id,
        name: payload.mode.name,
        companyName: payload.mode.company_name,
        tagline: payload.mode.tagline,
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
        backgroundImage: payload.mode.background_image ?? undefined,
        heroImage: payload.mode.hero_image ?? undefined,
        chatImage: payload.mode.chat_image ?? undefined,
      }
      setMode(newMode)
      // Clear visualization on mode switch
      setVisualization(null)
      setTabContentCache({})
      setActiveTab('dashboard')

      // Set up dashboard like New Conversation: use mode's default metrics
      setDashboardMetrics(newMode.defaultMetrics)
      if (payload.persona) {
        setPersona(payload.persona)
      }

      // Set welcome message like New Conversation does
      setMessages([{
        id: '1',
        role: 'assistant',
        content: `Hello! I'm your assistant at ${newMode.companyName}. How can I help you today?`,
        timestamp: new Date()
      }])

      // Keep blocking for 1 second to let any in-flight old messages drain
      setTimeout(() => {
        isSwitchingModeRef.current = false
      }, 1000)
    }
  }, [setMode])

  const { status, send } = useWebSocket({ onMessage: handleMessage })

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

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
      content: `Hello! I'm your assistant at ${mode.companyName}. How can I help you today?`,
      timestamp: new Date()
    }])
    // Reset visualization and metrics to current mode defaults
    setVisualization(null)
    setDashboardMetrics(mode.defaultMetrics)
    // Tell backend to clear history
    send({ type: 'clear_chat', payload: {} })
    // Clear tab content cache
    setTabContentCache({})
    setActiveTab('dashboard')
  }

  // Ref to track which mode's prefetch is active (for cancellation on mode switch)
  const prefetchModeIdRef = useRef<string | null>(null)

  const fetchTabContent = useCallback(async (tabId: string, tabLabel: string, modeId: string): Promise<ReactNode | null> => {
    try {
      const res = await fetch('http://localhost:8000/api/tab-content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tab_id: tabId, tab_label: tabLabel, mode_id: modeId }),
      })
      const data = await res.json()

      const nodes: ReactNode[] = []
      for (const tr of data.tool_results ?? []) {
        if (tr.tool === 'show_chart') {
          nodes.push(
            <ChartRenderer
              key={`${tabId}-chart-${nodes.length}`}
              chartType={tr.result.chart_type}
              title={tr.result.title}
              data={tr.result.data}
            />
          )
        }
      }

      return nodes.length > 0 ? nodes : null
    } catch (err) {
      console.error(`Failed to generate tab content for ${tabId}:`, err)
      return null
    }
  }, [])

  const prefetchAllTabs = useCallback(async (tabs: Array<{ id: string; label: string }>, modeId: string) => {
    prefetchModeIdRef.current = modeId
    for (const tab of tabs) {
      if (tab.id === 'dashboard' || tab.id === 'settings') continue
      // Abort if mode switched while prefetching
      if (prefetchModeIdRef.current !== modeId) return
      const content = await fetchTabContent(tab.id, tab.label, modeId)
      // Check again after await — mode may have switched during fetch
      if (prefetchModeIdRef.current !== modeId) return
      if (content) {
        setTabContentCache(prev => ({ ...prev, [tab.id]: content }))
      }
    }
  }, [fetchTabContent])

  // Prefetch all tab content in the background when mode is ready
  useEffect(() => {
    if (!isLoading && mode.tabs.length > 0) {
      prefetchAllTabs(mode.tabs, mode.id)
    }
  }, [isLoading, mode.id, mode.tabs, prefetchAllTabs])

  const generateTabContent = useCallback(async (tabId: string, tabLabel: string) => {
    // Cache hit — return immediately
    if (tabContentCache[tabId]) return

    setTabLoading(true)
    try {
      const content = await fetchTabContent(tabId, tabLabel, mode.id)
      if (content) {
        setTabContentCache(prev => ({ ...prev, [tabId]: content }))
      }
    } finally {
      setTabLoading(false)
    }
  }, [tabContentCache, mode.id, fetchTabContent])

  const handleTabClick = useCallback((tabId: string, tabLabel: string) => {
    setActiveTab(tabId)
    if (tabId !== 'dashboard' && tabId !== 'settings') {
      generateTabContent(tabId, tabLabel)
    }
  }, [generateTabContent])

  return (
    <div className="app">
      {/* Left Panel - Chat */}
      <aside
        className={`chat-panel${mode.chatImage ? ' has-chat-image' : ''}`}
        style={mode.chatImage ? {
          backgroundImage: `url(http://localhost:8000${mode.chatImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        } : undefined}
      >
        <header className="chat-header">
          <span className="header-title">{mode.companyName}</span>
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
            <button className="icon-button-img" onClick={handleNewChat} title="New Conversation">
              <img src="/icons/new_conversation.png" alt="New Conversation" className="button-icon" />
            </button>
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
            id="chat-message-input"
            name="chat-message"
            className="chat-input"
            placeholder="Chat with me here..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={status !== 'connected'}
            autoComplete="off"
            autoCorrect="off"
            data-lpignore="true"
            data-1p-ignore="true"
            data-bwignore="true"
            data-form-type="other"
            aria-label="Chat message"
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
      <main
        className={`dashboard-panel${mode.backgroundImage ? ' has-bg-image' : ''}`}
        style={mode.backgroundImage ? {
          backgroundImage: `url(http://localhost:8000${mode.backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        } : undefined}
      >
        {/* Mode generating overlay */}
        {modeGenerating && (
          <div className="mode-generating-overlay">
            <div className="mode-generating-content">
              <div className="mode-generating-spinner"></div>
              <p>{modeGenerating === 'new mode' ? 'Generating new mode...' : `Generating ${modeGenerating} mode...`}</p>
            </div>
          </div>
        )}
        {activeTab === 'dashboard' && (
          <Dashboard
            metrics={dashboardMetrics}
            visualization={visualization}
            companyName={mode.companyName}
            tagline={mode.tagline}
            heroImage={mode.heroImage ? `http://localhost:8000${mode.heroImage}` : undefined}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsPanel />
        )}
        {activeTab !== 'dashboard' && activeTab !== 'settings' && (
          <div className="tab-content-container">
            {tabLoading && !tabContentCache[activeTab] ? (
              <div className="visualization-loading">
                <div className="visualization-loading-spinner"></div>
                <p>Generating content...</p>
              </div>
            ) : tabContentCache[activeTab] ? (
              <div className="tab-content-visualization">
                {tabContentCache[activeTab]}
              </div>
            ) : (
              <div className="visualization-loading">
                <p>Click to load content for this tab.</p>
              </div>
            )}
          </div>
        )}

        <nav className="bottom-tabs">
          {mode.tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.id, tab.label)}
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
