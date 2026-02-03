import type { ReactNode } from 'react'

export interface VisualizationAreaProps {
  content?: ReactNode
  title?: string
  companyName?: string
  tagline?: string
}

export function VisualizationArea({ content, title, companyName, tagline }: VisualizationAreaProps) {
  return (
    <div className="visualization-container">
      {title && <h3 className="visualization-title">{title}</h3>}
      <div className="visualization-content">
        {content ? (
          content
        ) : (
          <div className="visualization-placeholder">
            <div className="company-logo">
              <span className="logo-icon">🏢</span>
            </div>
            <h2 className="company-name">{companyName || 'Welcome'}</h2>
            <p className="company-tagline">{tagline || 'Your trusted partner'}</p>
            <p className="viz-hint">Charts and data will appear here based on your queries.</p>
          </div>
        )}
      </div>
    </div>
  )
}
