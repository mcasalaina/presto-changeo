export interface ModeTheme {
  primary: string      // Main brand color (e.g., #1E88E5 for banking)
  secondary: string    // Accent color
  background: string   // Dashboard background
  surface: string      // Card/panel background
  text: string         // Primary text color
  textMuted: string    // Secondary text color
}

export interface ModeTab {
  id: string
  label: string
  icon: string         // Emoji icon
}

export interface Mode {
  id: string           // 'banking' | 'insurance' | 'healthcare'
  name: string         // Display name: "Banking", "Insurance", etc.
  theme: ModeTheme
  tabs: ModeTab[]
  systemPrompt: string // AI personality prompt for this mode
  defaultMetrics: Array<{ label: string; value: string | number; unit?: string }>
}
