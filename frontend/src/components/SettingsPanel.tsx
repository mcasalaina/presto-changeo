import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000'

interface VoicePreferenceResponse {
  voice: string
  available: string[]
}

export function SettingsPanel() {
  const [currentVoice, setCurrentVoice] = useState<string>('verse')
  const [availableVoices, setAvailableVoices] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/api/voice-preference`)
      .then(res => res.json())
      .then((data: VoicePreferenceResponse) => {
        setCurrentVoice(data.voice)
        setAvailableVoices(data.available)
      })
      .catch(err => console.error('Failed to load voice preference:', err))
  }, [])

  const selectVoice = async (voice: string) => {
    if (voice === currentVoice || saving) return
    setSaving(true)
    try {
      const res = await fetch(`${API_BASE}/api/voice-preference`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice }),
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setCurrentVoice(voice)
      }
    } catch (err) {
      console.error('Failed to save voice preference:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="settings-panel">
      <h2 className="settings-title">Settings</h2>
      <div className="settings-section">
        <h3 className="settings-section-title">Voice</h3>
        <p className="settings-section-desc">Choose the voice for AI assistant responses.</p>
        <div className="voice-options">
          {availableVoices.map(voice => (
            <button
              key={voice}
              className={`voice-option ${currentVoice === voice ? 'active' : ''}`}
              onClick={() => selectVoice(voice)}
              disabled={saving}
            >
              {voice}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
