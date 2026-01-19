import type { ReactNode } from 'react'
import { MetricsPanel, type Metric } from './MetricsPanel'
import { VisualizationArea } from './VisualizationArea'

export interface DashboardProps {
  metrics?: Metric[]
  visualization?: ReactNode
}

export function Dashboard({ metrics, visualization }: DashboardProps) {
  // When visualization is present, hide metrics and show chart full-width
  const hasVisualization = visualization != null

  return (
    <div className={`dashboard-container ${hasVisualization ? 'dashboard-chart-mode' : ''}`}>
      {!hasVisualization && (
        <div className="dashboard-metrics">
          <MetricsPanel metrics={metrics} />
        </div>
      )}
      <div className="dashboard-visualization">
        <VisualizationArea content={visualization} />
      </div>
    </div>
  )
}
