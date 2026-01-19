import type { Persona, BankingPersona, InsurancePersona, HealthcarePersona } from '../types/mode'

interface PersonaCardProps {
  persona: Persona
  modeId: string
}

function isBankingPersona(persona: Persona): persona is BankingPersona {
  return persona !== null && 'checking_balance' in persona
}

function isInsurancePersona(persona: Persona): persona is InsurancePersona {
  return persona !== null && 'total_coverage' in persona
}

function isHealthcarePersona(persona: Persona): persona is HealthcarePersona {
  return persona !== null && 'member_id' in persona
}

function formatCurrency(value: number): string {
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

export function PersonaCard({ persona, modeId }: PersonaCardProps) {
  if (!persona) {
    return null
  }

  // Determine key stat based on mode
  let keyStat: string
  let keyLabel: string

  if (modeId === 'banking' && isBankingPersona(persona)) {
    keyStat = formatCurrency(persona.checking_balance)
    keyLabel = 'Checking'
  } else if (modeId === 'insurance' && isInsurancePersona(persona)) {
    keyStat = formatCurrency(persona.total_coverage)
    keyLabel = 'Coverage'
  } else if (modeId === 'healthcare' && isHealthcarePersona(persona)) {
    keyStat = persona.member_id
    keyLabel = 'Member ID'
  } else {
    // Fallback - should not happen if types are correct
    keyStat = ''
    keyLabel = ''
  }

  return (
    <div className="persona-card">
      <div className="persona-info">
        <span className="persona-icon">&#128100;</span>
        <span className="persona-name">{persona.name}</span>
      </div>
      {keyStat && (
        <div className="persona-stat">
          <span className="stat-label">{keyLabel}:</span>
          <span className="stat-value">{keyStat}</span>
        </div>
      )}
    </div>
  )
}
