import type { VoiceStatus } from '../hooks/useVoice'

export interface VoiceToggleProps {
  isEnabled: boolean
  isMuted: boolean
  isListening: boolean
  isSpeaking: boolean
  status: VoiceStatus
  onEnable: () => void
  onDisable: () => void
  onToggleMute: () => void
}

/**
 * Voice toggle UI with enable/disable, mute, and visual indicators.
 * Shows listening (user speaking) and speaking (AI responding) states.
 */
export function VoiceToggle({
  isEnabled,
  isMuted,
  isListening,
  isSpeaking,
  status,
  onEnable,
  onDisable,
  onToggleMute,
}: VoiceToggleProps) {
  // Determine button classes based on state
  const getButtonClasses = () => {
    const classes = ['voice-button']
    if (isEnabled) {
      classes.push('active')
      if (isListening) classes.push('listening')
      if (isSpeaking) classes.push('speaking')
    }
    if (status === 'connecting') classes.push('connecting')
    if (status === 'error') classes.push('error')
    return classes.join(' ')
  }

  const handleMainClick = () => {
    if (status === 'connecting') return // Prevent double-click during connection
    if (isEnabled) {
      onDisable()
    } else {
      onEnable()
    }
  }

  // Status text for accessibility and visual feedback
  const getStatusText = () => {
    if (status === 'connecting') return 'Connecting...'
    if (status === 'error') return 'Error'
    if (!isEnabled) return ''
    if (isListening) return 'Listening...'
    if (isSpeaking) return 'Speaking...'
    return 'Voice active'
  }

  const statusText = getStatusText()

  return (
    <div className="voice-toggle">
      {/* Main voice toggle button */}
      <button
        className={getButtonClasses()}
        onClick={handleMainClick}
        title={isEnabled ? 'Disable voice' : 'Enable voice'}
        aria-label={isEnabled ? 'Disable voice mode' : 'Enable voice mode'}
        disabled={status === 'connecting'}
      >
        {status === 'connecting' ? (
          // Simple spinner during connection
          <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>
            ⟳
          </span>
        ) : status === 'error' ? (
          '!'
        ) : (
          '🎤'
        )}
      </button>

      {/* Mute button - only visible when voice is enabled */}
      {isEnabled && status === 'connected' && (
        <button
          className={`mute-button ${isMuted ? 'muted' : ''}`}
          onClick={onToggleMute}
          title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
        >
          {isMuted ? '🔇' : '🔊'}
        </button>
      )}

      {/* Status indicator text */}
      {statusText && (
        <span className="voice-status" aria-live="polite">
          {statusText}
        </span>
      )}
    </div>
  )
}
