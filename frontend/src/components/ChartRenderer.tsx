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

export function ChartRenderer({ chartType, title, data }: ChartRendererProps) {
  const [animated, setAnimated] = useState(false)

  // Trigger animation on mount
  useEffect(() => {
    // Small delay to ensure CSS transition can capture the change
    const timer = setTimeout(() => setAnimated(true), 50)
    return () => clearTimeout(timer)
  }, [])

  // Find max value for proportional bar widths
  const maxValue = Math.max(...data.map(d => d.value), 1)

  return (
    <div className="chart-container">
      <div className="chart-title">{title}</div>
      <div className="chart-subtitle">Type: {chartType}</div>
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
              <span className="chart-value">{item.value}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
