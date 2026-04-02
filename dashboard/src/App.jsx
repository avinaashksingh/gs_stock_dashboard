import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts'
import { Timer, RefreshCw, BarChart3, TrendingUp, Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react'

const COLORS = {
  black: '#000000',
  white: '#e1e4e8',
  sage: '#9ca393',
  slate: '#939ca3',
  darkSlate: '#646f77',
  blueGray: '#b5bdc4',
  mauveGray: '#c4b5bd',
  neutral: '#aeb4ac'
}

const ChartCard = ({ title, data, dataKey, color, unit = "" }) => (
  <div className="chart-card glass">
    <div className="chart-header">
      <h3>{title}</h3>
      <div className="chart-value">
        {data.length > 0 && data[data.length - 1][dataKey]?.toLocaleString()} {unit}
      </div>
    </div>
    <div className="chart-body">
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`color-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.darkSlate} vertical={false} opacity={0.2} />
          <XAxis 
            dataKey="Date" 
            hide 
          />
          <YAxis 
            hide 
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: COLORS.black, borderColor: COLORS.darkSlate, color: COLORS.white }}
            itemStyle={{ color: COLORS.white }}
            labelStyle={{ display: 'none' }}
          />
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color} 
            fillOpacity={1} 
            fill={`url(#color-${dataKey})`} 
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </div>
)

function App() {
  const [data, setData] = useState([])
  const [latest, setLatest] = useState(null)
  const [lastRefreshed, setLastRefreshed] = useState(new Date())
  const [secondsSinceRefresh, setSecondsSinceRefresh] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8080/yahoo-finance/latest')
      setData(response.data.data)
      setLatest(response.data.latest)
      setLastRefreshed(new Date())
      setSecondsSinceRefresh(0)
    } catch (error) {
      console.error("Error fetching stock data:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsSinceRefresh(Math.floor((new Date() - lastRefreshed) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [lastRefreshed])

  return (
    <div className="dashboard-container">
      <header className="dashboard-header glass">
        <div className="logo">
          <BarChart3 size={24} color={COLORS.sage} />
          <h1>GS Stock Generator</h1>
        </div>
        
        <div className="stats-header">
          <div className="stat-item">
            <Timer size={18} color={COLORS.slate} />
            <span>Refreshed <span className="highlight">{secondsSinceRefresh}s</span> ago</span>
          </div>
          <div className={`refresh-indicator ${loading ? 'spinning' : ''}`}>
            <RefreshCw size={18} color={COLORS.sage} />
          </div>
        </div>
      </header>

      <main className="dashboard-grid">
        <section className="summary-section">
          <div className="latest-card glass highlight-border">
            <div className="card-header">
              <TrendingUp size={20} color={COLORS.sage} />
              <h2>Real-time Summary</h2>
            </div>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="label">Latest Close</span>
                <span className="value">${latest?.Close?.toFixed(2)}</span>
              </div>
              <div className="summary-item">
                <span className="label">Daily High</span>
                <span className="value">${latest?.High?.toFixed(2)}</span>
              </div>
              <div className="summary-item">
                <span className="label">Trading Volume</span>
                <span className="value">{latest?.Volume?.toLocaleString()}</span>
              </div>
              <div className="summary-item">
                <span className="label">Timestamp</span>
                <span className="value small-text">{latest?.Date}</span>
              </div>
            </div>
          </div>
        </section>

        <section className="charts-section">
          <ChartCard title="Opening Price" data={data} dataKey="Open" color={COLORS.sage} unit="$" />
          <ChartCard title="Closing Price" data={data} dataKey="Close" color={COLORS.slate} unit="$" />
          <ChartCard title="High" data={data} dataKey="High" color={COLORS.blueGray} unit="$" />
          <ChartCard title="Low" data={data} dataKey="Low" color={COLORS.mauveGray} unit="$" />
          <ChartCard title="Volume" data={data} dataKey="Volume" color={COLORS.neutral} />
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>PostgreSQL Driven • Statistical Generator • "One In, One Out" Logic Active</p>
      </footer>
    </div>
  )
}

export default App
