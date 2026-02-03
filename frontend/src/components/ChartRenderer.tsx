import { useEffect, useState } from 'react'

interface ChartData {
  label: string
  value: number
}

interface ChartRendererProps {
  chartType: 'line' | 'bar' | 'pie' | 'area'
  title: string
  data: ChartData[]
}

/**
 * Format a number as currency if it looks like a dollar amount (> 100)
 * Otherwise format with commas
 */
function formatValue(value: number): string {
  if (value >= 100) {
    return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  }
  return value.toLocaleString('en-US')
}

/**
 * CSS-only chart renderer supporting bar (vertical/horizontal) and pie charts
 */
export function ChartRenderer({ chartType, title, data }: ChartRendererProps) {
  const [animated, setAnimated] = useState(false)

  // Trigger animation on mount
  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 50)
    return () => clearTimeout(timer)
  }, [])

  // Find max value for proportional sizing
  const maxValue = Math.max(...data.map(d => d.value), 1)
  const total = data.reduce((sum, d) => sum + d.value, 0)

  // Use vertical bars for bar charts with < 5 items, horizontal otherwise
  const useVerticalBars = chartType === 'bar' && data.length < 5

  // Pie chart rendering
  if (chartType === 'pie') {
    // Calculate pie segments using conic-gradient
    let currentAngle = 0
    const colors = ['#7B1FA2', '#00897B', '#E53935', '#1E88E5', '#43A047', '#FB8C00']
    const segments = data.map((item, index) => {
      const percentage = (item.value / total) * 100
      const startAngle = currentAngle
      currentAngle += percentage * 3.6 // Convert percentage to degrees
      return {
        ...item,
        percentage,
        startAngle,
        endAngle: currentAngle,
        color: colors[index % colors.length]
      }
    })

    const gradientStops = segments.map((seg, i) => {
      const start = i === 0 ? 0 : segments[i - 1].endAngle
      return `${seg.color} ${start}deg ${seg.endAngle}deg`
    }).join(', ')

    return (
      <div className="chart-container">
        <div className="chart-title">{title}</div>
        <div className="pie-chart-wrapper">
          <div
            className="pie-chart"
            style={{
              background: animated
                ? `conic-gradient(${gradientStops})`
                : 'var(--color-surface)',
              transition: 'background 0.5s ease-out'
            }}
          />
          <div className="pie-legend">
            {segments.map((item, index) => (
              <div key={index} className="pie-legend-item">
                <span
                  className="pie-legend-color"
                  style={{ backgroundColor: item.color }}
                />
                <span className="pie-legend-label">{item.label}</span>
                <span className="pie-legend-value">{formatValue(item.value)}</span>
                <span className="pie-legend-percent">({item.percentage.toFixed(1)}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Vertical bar chart
  if (useVerticalBars) {
    return (
      <div className="chart-container">
        <div className="chart-title">{title}</div>
        <div className="vertical-bars">
          {data.map((item, index) => {
            const heightPercent = (item.value / maxValue) * 100
            return (
              <div key={index} className="vertical-bar-column">
                <span className="vertical-bar-value">{formatValue(item.value)}</span>
                <div className="vertical-bar-track">
                  <div
                    className="vertical-bar"
                    style={{
                      height: animated ? `${heightPercent}%` : '0%',
                      transitionDelay: `${index * 0.1}s`
                    }}
                  />
                </div>
                <span className="vertical-bar-label">{item.label}</span>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Horizontal bar chart (default for bar, line, area with 5+ items)
  return (
    <div className="chart-container">
      <div className="chart-title">{title}</div>
      <div className="chart-bars">
        {data.map((item, index) => {
          const widthPercent = (item.value / maxValue) * 100
          return (
            <div key={index} className="chart-bar-row">
              <span className="chart-label">{item.label}</span>
              <div className="chart-bar-container">
                <div
                  className="chart-bar"
                  style={{
                    width: animated ? `${widthPercent}%` : '0%',
                    transitionDelay: `${index * 0.1}s`
                  }}
                />
              </div>
              <span className="chart-value">{formatValue(item.value)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
