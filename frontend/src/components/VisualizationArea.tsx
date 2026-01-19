import type { ReactNode } from 'react'

export interface VisualizationAreaProps {
  content?: ReactNode
  title?: string
}

export function VisualizationArea({ content, title }: VisualizationAreaProps) {
  return (
    <div className="visualization-container">
      {title && <h3 className="visualization-title">{title}</h3>}
      <div className="visualization-content">
        {content ? (
          content
        ) : (
          <div className="visualization-placeholder">
            <div className="viz-icon">📊</div>
            <h2>Welcome</h2>
            <p>Say "Presto-Change-O, you're a bank" to transform this interface.</p>
            <p className="viz-hint">Charts and data will appear here based on your queries.</p>
          </div>
        )}
      </div>
    </div>
  )
}
