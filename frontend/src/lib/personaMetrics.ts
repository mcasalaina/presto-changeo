import type { Persona, BankingPersona, InsurancePersona, HealthcarePersona } from '../types/mode'
import type { Metric } from '../components/MetricsPanel'

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

/**
 * Generate dashboard metrics from persona data to ensure consistency.
 * The metrics displayed on the dashboard will match the persona card header.
 */
export function getMetricsFromPersona(persona: Persona, modeId: string): Metric[] {
  if (!persona) {
    return []
  }

  if (modeId === 'banking' && isBankingPersona(persona)) {
    return [
      { label: 'Checking Balance', value: formatCurrency(persona.checking_balance) },
      { label: 'Savings Balance', value: formatCurrency(persona.savings_balance) },
      { label: 'Credit Score', value: persona.credit_score },
      { label: 'Credit Limit', value: formatCurrency(persona.credit_limit) },
    ]
  }

  if (modeId === 'insurance' && isInsurancePersona(persona)) {
    const pendingClaims = persona.claims_history.filter(c => c.status === 'pending').length
    return [
      { label: 'Active Policies', value: persona.active_policies.length },
      { label: 'Total Coverage', value: formatCurrency(persona.total_coverage) },
      { label: 'Pending Claims', value: pendingClaims },
      { label: 'Next Premium', value: formatCurrency(persona.monthly_premium), unit: '/mo' },
    ]
  }

  if (modeId === 'healthcare' && isHealthcarePersona(persona)) {
    const deductiblePercent = Math.round((persona.deductible_met / persona.deductible) * 100)
    return [
      { label: 'Deductible Progress', value: `${deductiblePercent}%` },
      { label: 'Deductible Met', value: formatCurrency(persona.deductible_met) },
      { label: 'Upcoming Appointments', value: persona.upcoming_appointments.length },
      { label: 'Active Prescriptions', value: persona.active_prescriptions.length },
    ]
  }

  return []
}
