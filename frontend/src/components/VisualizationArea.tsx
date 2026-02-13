import { useState, type ReactNode } from 'react'

export interface VisualizationAreaProps {
  content?: ReactNode
  title?: string
  companyName?: string
  tagline?: string
  heroImage?: string
}

export function VisualizationArea({ content, title, companyName, tagline, heroImage }: VisualizationAreaProps) {
  const [heroError, setHeroError] = useState(false)
  const hasHero = heroImage && !heroError

  return (
    <div
      className={`visualization-container${hasHero ? ' has-hero-bg' : ''}`}
      style={hasHero ? {
        backgroundImage: `url(${heroImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      } : undefined}
    >
      {/* Hidden img to detect load errors */}
      {heroImage && !heroError && (
        <img
          src={heroImage}
          alt=""
          style={{ display: 'none' }}
          onError={() => setHeroError(true)}
        />
      )}
      {title && <h3 className="visualization-title">{title}</h3>}
      <div className="visualization-content">
        {content ? (
          content
        ) : (
          <div className="visualization-placeholder">
            {!hasHero && (
              <div className="company-logo">
                <span className="logo-icon">🏢</span>
              </div>
            )}
            <h2 className="company-name">{companyName || 'Welcome'}</h2>
            <p className="company-tagline">{tagline || 'Your trusted partner'}</p>
            <p className="viz-hint">Charts and data will appear here based on your queries.</p>
          </div>
        )}
      </div>
    </div>
  )
}
