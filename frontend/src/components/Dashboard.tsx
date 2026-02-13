import type { ReactNode } from 'react'
import { MetricsPanel, type Metric } from './MetricsPanel'
import { VisualizationArea } from './VisualizationArea'

export interface DashboardProps {
  metrics?: Metric[]
  visualization?: ReactNode
  companyName?: string
  tagline?: string
  heroImage?: string
}

export function Dashboard({ metrics, visualization, companyName, tagline, heroImage }: DashboardProps) {
  // When visualization is present, hide metrics and show chart full-width
  const hasVisualization = visualization != null
  // Check if there are actual metrics to display
  const hasMetrics = metrics && metrics.length > 0
  // Full width mode: either showing a chart OR no metrics to display
  const fullWidthMode = hasVisualization || !hasMetrics

  return (
    <div className={`dashboard-container ${fullWidthMode ? 'dashboard-full-width' : ''}`}>
      {!fullWidthMode && (
        <div className="dashboard-metrics">
          <MetricsPanel metrics={metrics} />
        </div>
      )}
      <div className="dashboard-visualization">
        <VisualizationArea
          content={visualization}
          companyName={companyName}
          tagline={tagline}
          heroImage={heroImage}
        />
      </div>
    </div>
  )
}
