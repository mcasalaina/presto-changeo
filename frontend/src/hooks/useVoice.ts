import { useState, useRef, useCallback, useEffect } from 'react'
import { pcm16ToFloat32, float32ToPcm16Base64, VOICE_SAMPLE_RATE } from '../lib/audioUtils'

const VOICE_WS_URL = 'ws://localhost:8000/voice'
const MAX_RECONNECT_DELAY = 30000
const INITIAL_RECONNECT_DELAY = 1000

export type VoiceStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface UseVoiceOptions {
  onTranscript?: (role: 'user' | 'assistant', text: string) => void
  onToolResult?: (tool: string, result: Record<string, unknown>) => void
  onModeSwitch?: (payload: Record<string, unknown>) => void  // Called when mode switch detected via voice
  onModeGenerating?: (industry: string) => void  // Called when mode generation starts
  onError?: (error: string) => void
  onInterrupt?: () => void  // Called when user starts speaking (interrupts assistant)
  onUserSpeechEnd?: () => void  // Called when user stops speaking (end of utterance)
  onUserSpeechStart?: () => void  // Called when user starts speaking (create placeholder)
}

export interface UseVoiceReturn {
  // State
  isEnabled: boolean
  isMuted: boolean
  isListening: boolean
  isSpeaking: boolean
  status: VoiceStatus

  // Actions
  enable: () => Promise<void>
  disable: () => void
  toggleMute: () => void
}

interface VoiceMessage {
  type: string
  [key: string]: unknown
}

/**
 * React hook for voice interaction with gpt-realtime.
 * Handles microphone capture, audio playback, and WebSocket communication.
 *
 * @param options - Callbacks for transcript and tool results
 * @returns Voice state and control functions
 */
export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
  const { onTranscript, onToolResult, onModeSwitch, onModeGenerating, onError, onInterrupt, onUserSpeechEnd, onUserSpeechStart } = options

  // State
  const [isEnabled, setIsEnabled] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [status, setStatus] = useState<VoiceStatus>('disconnected')

  // Refs for cleanup and callbacks
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const playbackContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY)
  const shouldReconnectRef = useRef(false)
  const isMutedRef = useRef(false)
  const speakingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Audio playback queue and scheduling
  const audioQueueRef = useRef<Float32Array[]>([])
  const isPlayingRef = useRef(false)
  const nextPlayTimeRef = useRef(0)  // Scheduled time for next chunk

  // Keep refs in sync with state
  isMutedRef.current = isMuted

  // Store callbacks in refs to avoid stale closures
  const onTranscriptRef = useRef(onTranscript)
  const onToolResultRef = useRef(onToolResult)
  const onModeSwitchRef = useRef(onModeSwitch)
  const onModeGeneratingRef = useRef(onModeGenerating)
  const onErrorRef = useRef(onError)
  const onInterruptRef = useRef(onInterrupt)
  const onUserSpeechEndRef = useRef(onUserSpeechEnd)
  const onUserSpeechStartRef = useRef(onUserSpeechStart)
  onTranscriptRef.current = onTranscript
  onToolResultRef.current = onToolResult
  onModeSwitchRef.current = onModeSwitch
  onModeGeneratingRef.current = onModeGenerating
  onErrorRef.current = onError
  onInterruptRef.current = onInterrupt
  onUserSpeechEndRef.current = onUserSpeechEnd
  onUserSpeechStartRef.current = onUserSpeechStart

  // Track current audio source for interruption
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null)

  /**
   * Stop all audio playback and clear queue (for interruption)
   */
  const stopPlayback = useCallback(() => {
    // Stop currently playing audio
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop()
      } catch {
        // Already stopped
      }
      currentSourceRef.current = null
    }
    // Clear queue and reset scheduling
    audioQueueRef.current = []
    nextPlayTimeRef.current = 0
    isPlayingRef.current = false
    setIsSpeaking(false)
  }, [])

  /**
   * Play queued audio chunks with precise scheduling for gapless playback
   */
  const playNextAudioChunk = useCallback(() => {
    const playbackContext = playbackContextRef.current
    if (!playbackContext || playbackContext.state === 'closed') {
      return
    }

    // Process all queued chunks and schedule them
    while (audioQueueRef.current.length > 0) {
      const float32 = audioQueueRef.current.shift()!

      // Create audio buffer from Float32Array
      const buffer = playbackContext.createBuffer(1, float32.length, VOICE_SAMPLE_RATE)
      buffer.getChannelData(0).set(float32)

      // Calculate duration of this chunk
      const duration = float32.length / VOICE_SAMPLE_RATE

      // Schedule to play at the right time (gapless)
      const now = playbackContext.currentTime
      const startTime = Math.max(now, nextPlayTimeRef.current)

      // Create source node and schedule
      const source = playbackContext.createBufferSource()
      currentSourceRef.current = source
      source.buffer = buffer
      source.connect(playbackContext.destination)
      source.start(startTime)

      // Update next play time for seamless scheduling
      nextPlayTimeRef.current = startTime + duration
      isPlayingRef.current = true
    }
  }, [])

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data) as VoiceMessage

      switch (message.type) {
        case 'status':
          if (message.status === 'connected') {
            setStatus('connected')
            reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
          } else if (message.status === 'error') {
            setStatus('error')
            onErrorRef.current?.(message.error as string || 'Connection error')
          }
          break

        case 'speech_started':
          setIsListening(true)
          // Stop assistant audio playback when user starts speaking (interruption)
          stopPlayback()
          onInterruptRef.current?.()
          onUserSpeechStartRef.current?.()
          break

        case 'speech_stopped':
          setIsListening(false)
          onUserSpeechEndRef.current?.()
          break

        case 'audio': {
          // Queue audio for playback
          const base64 = message.data as string
          const float32 = pcm16ToFloat32(base64)
          audioQueueRef.current.push(float32)
          playNextAudioChunk()

          // Set speaking state with timeout to detect end of speech
          setIsSpeaking(true)
          if (speakingTimeoutRef.current) {
            clearTimeout(speakingTimeoutRef.current)
          }
          speakingTimeoutRef.current = setTimeout(() => {
            setIsSpeaking(false)
          }, 500) // Consider stopped speaking after 500ms of no audio
          break
        }

        case 'transcript':
          onTranscriptRef.current?.(
            message.role as 'user' | 'assistant',
            message.text as string
          )
          break

        case 'tool_result':
          onToolResultRef.current?.(
            message.tool as string,
            message.result as Record<string, unknown>
          )
          break

        case 'mode_switch':
          onModeSwitchRef.current?.(message.payload as Record<string, unknown>)
          break

        case 'mode_generating':
          onModeGeneratingRef.current?.((message.payload as { industry: string }).industry)
          break

        case 'mode_generating_cancel':
          // Signal to clear the mode generating indicator (pass empty string)
          onModeGeneratingRef.current?.('')
          break

        case 'error':
          onErrorRef.current?.(message.error as string)
          break
      }
    } catch (err) {
      console.warn('Failed to parse voice message:', err)
    }
  }, [playNextAudioChunk, stopPlayback])

  /**
   * Connect to voice WebSocket
   */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    setStatus('connecting')
    const ws = new WebSocket(VOICE_WS_URL)

    ws.onopen = () => {
      // Status will be set to 'connected' when we receive status message from server
    }

    ws.onclose = () => {
      setStatus('disconnected')
      setIsListening(false)
      setIsSpeaking(false)

      // Reconnect with exponential backoff if should reconnect
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(
            reconnectDelayRef.current * 2,
            MAX_RECONNECT_DELAY
          )
          connectWebSocket()
        }, reconnectDelayRef.current)
      }
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onmessage = handleMessage

    wsRef.current = ws
  }, [handleMessage])

  /**
   * Start microphone capture and send audio to backend
   */
  const startMicCapture = useCallback(async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream

      // Create AudioContext for mic input
      // Note: We use default sample rate and let the backend handle resampling if needed
      const audioContext = new AudioContext({ sampleRate: VOICE_SAMPLE_RATE })
      audioContextRef.current = audioContext

      // Create source from microphone stream
      const source = audioContext.createMediaStreamSource(stream)

      // Create ScriptProcessor to access raw audio samples
      // Buffer size 4096, mono input, mono output
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (e) => {
        // Only send if not muted and WebSocket is connected
        if (!isMutedRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0)
          const pcm16Base64 = float32ToPcm16Base64(inputData)
          wsRef.current.send(JSON.stringify({ type: 'audio', data: pcm16Base64 }))
        }
      }

      // Connect: source -> processor -> destination (required for onaudioprocess to fire)
      source.connect(processor)
      processor.connect(audioContext.destination)

    } catch (err) {
      console.error('Failed to start mic capture:', err)
      onErrorRef.current?.('Microphone access denied or unavailable')
      throw err
    }
  }, [])

  /**
   * Stop microphone capture and cleanup
   */
  const stopMicCapture = useCallback(() => {
    // Stop media stream tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }

    // Disconnect and cleanup processor
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
  }, [])

  /**
   * Enable voice mode - start WebSocket, mic capture, and playback
   */
  const enable = useCallback(async () => {
    if (isEnabled) return

    try {
      // Create playback AudioContext
      playbackContextRef.current = new AudioContext({ sampleRate: VOICE_SAMPLE_RATE })

      // Start mic capture first (may throw if permission denied)
      await startMicCapture()

      // Connect WebSocket
      shouldReconnectRef.current = true
      connectWebSocket()

      setIsEnabled(true)
      setIsMuted(false)
    } catch (err) {
      // Cleanup on failure
      stopMicCapture()
      if (playbackContextRef.current && playbackContextRef.current.state !== 'closed') {
        playbackContextRef.current.close()
        playbackContextRef.current = null
      }
      throw err
    }
  }, [isEnabled, startMicCapture, connectWebSocket, stopMicCapture])

  /**
   * Disable voice mode - cleanup everything
   */
  const disable = useCallback(() => {
    // Prevent reconnection
    shouldReconnectRef.current = false

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Clear speaking timeout
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current)
      speakingTimeoutRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Stop mic capture
    stopMicCapture()

    // Close playback context
    if (playbackContextRef.current && playbackContextRef.current.state !== 'closed') {
      playbackContextRef.current.close()
      playbackContextRef.current = null
    }

    // Clear audio queue
    audioQueueRef.current = []
    isPlayingRef.current = false

    // Reset state
    setIsEnabled(false)
    setIsMuted(false)
    setIsListening(false)
    setIsSpeaking(false)
    setStatus('disconnected')
    reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
  }, [stopMicCapture])

  /**
   * Toggle mute - stop/start sending audio but keep connection alive
   * Updates ref immediately to prevent race conditions with audio processing
   */
  const toggleMute = useCallback(() => {
    const newMuted = !isMutedRef.current
    isMutedRef.current = newMuted  // Update ref immediately for audio processor
    setIsMuted(newMuted)  // Update state for UI
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disable()
    }
  }, [disable])

  return {
    isEnabled,
    isMuted,
    isListening,
    isSpeaking,
    status,
    enable,
    disable,
    toggleMute,
  }
}
