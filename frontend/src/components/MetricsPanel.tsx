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

export function MetricsPanel({ metrics = defaultMetrics }: MetricsPanelProps) {
  return (
    <div className="metrics-panel">
      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-card">
            <span className="metric-label">{metric.label}</span>
            <div className="metric-value-row">
              <span className="metric-value">{metric.value}</span>
              {metric.unit && <span className="metric-unit">{metric.unit}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
