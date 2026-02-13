import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { Mode, ModeTheme, Persona } from '../types/mode'

// Default banking mode (matches backend default)
const defaultMode: Mode = {
  id: 'banking',
  name: 'Banking',
  companyName: 'Meridian Trust Bank',
  tagline: 'Your trusted financial partner since 1952',
  theme: {
    primary: '#1E88E5',
    secondary: '#43A047',
    background: '#f8fafc',
    surface: '#ffffff',
    text: '#0f172a',
    textMuted: '#64748b',
  },
  tabs: [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'accounts', label: 'Accounts', icon: '💳' },
    { id: 'transfers', label: 'Transfers', icon: '💸' },
    { id: 'payments', label: 'Payments', icon: '📋' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ],
  systemPrompt: '',  // Not used on frontend
  defaultMetrics: [
    { label: 'Account Balance', value: '$24,856.42' },
    { label: 'Recent Transactions', value: 12 },
    { label: 'Pending Payments', value: 3 },
    { label: 'Credit Score', value: 742 },
  ],
}

interface ModeContextValue {
  mode: Mode
  setMode: (mode: Mode) => void
  persona: Persona
  isLoading: boolean
}

const ModeContext = createContext<ModeContextValue | null>(null)

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

function darkenColor(hex: string, amount: number): string {
  const rgb = hexToRgb(hex)
  if (!rgb) return hex
  const r = Math.max(0, Math.floor(rgb.r * (1 - amount)))
  const g = Math.max(0, Math.floor(rgb.g * (1 - amount)))
  const b = Math.max(0, Math.floor(rgb.b * (1 - amount)))
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

function applyTheme(theme: ModeTheme) {
  const root = document.documentElement
  root.style.setProperty('--theme-primary', theme.primary)
  root.style.setProperty('--theme-secondary', theme.secondary)
  root.style.setProperty('--theme-background', theme.background)
  root.style.setProperty('--theme-surface', theme.surface)
  root.style.setProperty('--theme-text', theme.text)
  root.style.setProperty('--theme-text-muted', theme.textMuted)
  // Chat sidebar uses a darker version of primary color
  root.style.setProperty('--theme-chat-bg', darkenColor(theme.primary, 0.4))
}

export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<Mode>(defaultMode)
  const [persona, setPersonaState] = useState<Persona>(null)
  const [isLoading, setIsLoading] = useState(true)

  const setMode = useCallback((newMode: Mode) => {
    setModeState(newMode)
    applyTheme(newMode.theme)
  }, [])

  // Fetch initial state from backend on mount
  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/state')
        if (response.ok) {
          const data = await response.json()

          // Transform backend snake_case to frontend camelCase
          const restoredMode: Mode = {
            id: data.mode.id,
            name: data.mode.name,
            companyName: data.mode.company_name,
            tagline: data.mode.tagline,
            theme: {
              primary: data.mode.theme.primary,
              secondary: data.mode.theme.secondary,
              background: data.mode.theme.background,
              surface: data.mode.theme.surface,
              text: data.mode.theme.text,
              textMuted: data.mode.theme.text_muted,
            },
            tabs: data.mode.tabs,
            systemPrompt: '',
            defaultMetrics: data.mode.defaultMetrics,
            backgroundImage: data.mode.background_image ?? undefined,
            heroImage: data.mode.hero_image ?? undefined,
            chatImage: data.mode.chat_image ?? undefined,
          }

          setModeState(restoredMode)
          applyTheme(restoredMode.theme)

          if (data.persona) {
            setPersonaState(data.persona)
          }
        }
      } catch (err) {
        console.warn('Failed to fetch initial state, using defaults:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchState()
  }, [])

  // Apply default theme on initial render (before fetch completes)
  useEffect(() => {
    applyTheme(defaultMode.theme)
  }, [])

  return (
    <ModeContext.Provider value={{ mode, setMode, persona, isLoading }}>
      {children}
    </ModeContext.Provider>
  )
}

export function useMode() {
  const context = useContext(ModeContext)
  if (!context) {
    throw new Error('useMode must be used within a ModeProvider')
  }
  return context
}
