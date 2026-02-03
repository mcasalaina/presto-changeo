import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend
} from 'recharts'

interface ChartData {
  label: string
  value: number
}

interface ChartRendererProps {
  chartType: 'line' | 'bar' | 'pie' | 'area'
  title: string
  data: ChartData[]
}

// Color palette for charts
const COLORS = ['#1E88E5', '#43A047', '#7B1FA2', '#E53935', '#00ACC1', '#FB8C00']

/**
 * Format a number as currency if it looks like a dollar amount (> 100)
 */
function formatValue(value: number): string {
  if (value >= 100) {
    return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  }
  return value.toLocaleString('en-US')
}

/**
 * Detect if data contains multi-series pattern (e.g., "Jan - Checking", "Jan - Savings")
 * Returns { isMultiSeries, series: string[], restructuredData }
 */
function detectMultiSeries(data: ChartData[]): {
  isMultiSeries: boolean
  series: string[]
  restructuredData: Record<string, unknown>[]
} {
  // Look for patterns like "time - series" or "time: series"
  const separators = [' - ', ': ', ' – ']
  let separator: string | null = null

  for (const sep of separators) {
    if (data.every(d => d.label.includes(sep))) {
      separator = sep
      break
    }
  }

  if (!separator) {
    return {
      isMultiSeries: false,
      series: [],
      restructuredData: data.map(d => ({ name: d.label, value: d.value }))
    }
  }

  // Extract unique time points and series names
  const timePoints = new Map<string, Record<string, unknown>>()
  const seriesSet = new Set<string>()

  for (const d of data) {
    const parts = d.label.split(separator)
    if (parts.length === 2) {
      const [time, series] = parts
      seriesSet.add(series)

      if (!timePoints.has(time)) {
        timePoints.set(time, { name: time })
      }
      // Use series name as key, converting to lowercase for safety
      const seriesKey = series.toLowerCase().replace(/\s+/g, '_')
      timePoints.get(time)![seriesKey] = d.value
    }
  }

  const series = Array.from(seriesSet)
  const restructuredData = Array.from(timePoints.values())

  return {
    isMultiSeries: series.length > 1,
    series,
    restructuredData
  }
}

/**
 * Chart renderer using Recharts library with multi-series support
 */
export function ChartRenderer({ chartType, title, data }: ChartRendererProps) {
  // Detect and handle multi-series data
  const { isMultiSeries, series, restructuredData } = detectMultiSeries(data)

  // Custom tooltip formatter
  const tooltipFormatter = (value: number) => formatValue(value)

  // For multi-series line/area charts
  if ((chartType === 'line' || chartType === 'area') && isMultiSeries) {
    const seriesKeys = series.map(s => s.toLowerCase().replace(/\s+/g, '_'))

    return (
      <div className="chart-container">
        <div className="chart-title">{title}</div>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            {chartType === 'line' ? (
              <LineChart data={restructuredData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.3} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={formatValue} />
                <Tooltip formatter={tooltipFormatter} />
                <Legend />
                {seriesKeys.map((key, index) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={series[index]}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={3}
                    dot={{ fill: COLORS[index % COLORS.length], strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                ))}
              </LineChart>
            ) : (
              <AreaChart data={restructuredData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.3} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={formatValue} />
                <Tooltip formatter={tooltipFormatter} />
                <Legend />
                {seriesKeys.map((key, index) => (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={series[index]}
                    stroke={COLORS[index % COLORS.length]}
                    fill={COLORS[index % COLORS.length]}
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                ))}
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  // Single series charts
  const chartData = data.map(d => ({ name: d.label, value: d.value }))

  return (
    <div className="chart-container">
      <div className="chart-title">{title}</div>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          {chartType === 'line' ? (
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.3} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={formatValue} />
              <Tooltip formatter={tooltipFormatter} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#1E88E5"
                strokeWidth={3}
                dot={{ fill: '#1E88E5', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          ) : chartType === 'area' ? (
            <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.3} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={formatValue} />
              <Tooltip formatter={tooltipFormatter} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#1E88E5"
                fill="#1E88E5"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          ) : chartType === 'pie' ? (
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${formatValue(value)}`}
                outerRadius={100}
                dataKey="value"
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={tooltipFormatter} />
              <Legend />
            </PieChart>
          ) : (
            // Bar chart (default)
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.3} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={formatValue} />
              <Tooltip formatter={tooltipFormatter} />
              <Bar dataKey="value" fill="#1E88E5" radius={[4, 4, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
