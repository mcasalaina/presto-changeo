import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { Mode, ModeTheme } from '../types/mode'

// Default banking mode (matches backend default)
const defaultMode: Mode = {
  id: 'banking',
  name: 'Banking',
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
}

const ModeContext = createContext<ModeContextValue | null>(null)

function applyTheme(theme: ModeTheme) {
  const root = document.documentElement
  root.style.setProperty('--theme-primary', theme.primary)
  root.style.setProperty('--theme-secondary', theme.secondary)
  root.style.setProperty('--theme-background', theme.background)
  root.style.setProperty('--theme-surface', theme.surface)
  root.style.setProperty('--theme-text', theme.text)
  root.style.setProperty('--theme-text-muted', theme.textMuted)
}

export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<Mode>(defaultMode)

  const setMode = useCallback((newMode: Mode) => {
    setModeState(newMode)
    applyTheme(newMode.theme)
  }, [])

  return (
    <ModeContext.Provider value={{ mode, setMode }}>
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
