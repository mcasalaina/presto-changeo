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
  companyName: string  // Fake company name for branding: "Meridian Trust Bank"
  tagline: string      // Company tagline for welcome area
  theme: ModeTheme
  tabs: ModeTab[]
  systemPrompt: string // AI personality prompt for this mode
  defaultMetrics: Array<{ label: string; value: string | number; unit?: string }>
  backgroundImage?: string  // URL for dashboard background image
  heroImage?: string        // URL for hero/logo image in visualization area
  chatImage?: string        // URL for chat sidebar background image
}

// =============================================================================
// Persona Types (matching backend Pydantic models)
// =============================================================================

export interface BasePersona {
  name: string
  member_since?: string
}

export interface BankingPersona extends BasePersona {
  checking_balance: number
  savings_balance: number
  credit_score: number
  account_number_last4: string
  credit_limit: number
  recent_transactions: Array<{
    date: string
    description: string
    amount: number
    category: string
  }>
}

export interface InsurancePersona extends BasePersona {
  total_coverage: number
  monthly_premium: number
  active_policies: Array<{
    type: string
    coverage: number
    premium: number
    deductible: number
    policy_number: string
    renewal_date: string
  }>
  claims_history: Array<{
    claim_id: string
    date: string
    type: string
    amount: number
    status: string
  }>
  risk_score: string
}

export interface HealthcarePersona extends BasePersona {
  member_id: string
  date_of_birth: string
  primary_care_provider: string
  plan_name: string
  deductible: number
  deductible_met: number
  out_of_pocket_max: number
  out_of_pocket_spent: number
  upcoming_appointments: Array<{
    date: string
    time: string
    provider: string
    specialty: string
    location: string
  }>
  active_prescriptions: Array<{
    medication: string
    dosage: string
    frequency: string
    refills_remaining: number
  }>
}

export type Persona = BankingPersona | InsurancePersona | HealthcarePersona | null
