export interface Metric {
  label: string
  value: string | number
  unit?: string
}

export interface MetricsPanelProps {
  metrics?: Metric[]
}

const defaultMetrics: Metric[] = [
  { label: 'Location', value: '12.5', unit: 'Million Km' },
  { label: 'Temperature', value: '-66.34', unit: '°C' },
  { label: 'Angular Velocity', value: '285.46', unit: 'RPM' },
  { label: 'CPU Load', value: '19.88', unit: '%' },
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
