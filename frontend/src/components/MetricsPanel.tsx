export interface Metric {
  label: string
  value: string | number
  unit?: string
}

export interface MetricsPanelProps {
  metrics?: Metric[]
}

const defaultMetrics: Metric[] = [
  { label: 'Account Balance', value: '$24,856.42' },
  { label: 'Recent Transactions', value: '12' },
  { label: 'Pending Payments', value: '3' },
  { label: 'Credit Score', value: '742' },
]

/**
 * Format a metric value with its unit, handling currency as prefix.
 * Integers are displayed without decimals, floats keep their precision.
 */
function formatMetricValue(value: string | number, unit?: string): string {
  // If value is already a formatted string (e.g., "$24,856.42"), return as-is
  if (typeof value === 'string' && (value.includes('$') || value.includes('%'))) {
    return value
  }

  // Format number with thousands separators
  // Only show decimals if the value has them (not a whole number)
  let formattedNumber: string
  if (typeof value === 'number') {
    const isWholeNumber = Number.isInteger(value)
    formattedNumber = value.toLocaleString('en-US', {
      minimumFractionDigits: isWholeNumber ? 0 : 2,
      maximumFractionDigits: isWholeNumber ? 0 : 2
    })
  } else {
    formattedNumber = value
  }

  // Handle currency prefix
  if (unit === '$') {
    return `$${formattedNumber}`
  }

  // Handle percentage suffix
  if (unit === '%') {
    return `${formattedNumber}%`
  }

  // Handle other units as suffix
  if (unit) {
    return `${formattedNumber} ${unit}`
  }

  return String(formattedNumber)
}

export function MetricsPanel({ metrics = defaultMetrics }: MetricsPanelProps) {
  return (
    <div className="metrics-panel">
      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-card">
            <span className="metric-label">{metric.label}</span>
            <div className="metric-value-row">
              <span className="metric-value">{formatMetricValue(metric.value, metric.unit)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
