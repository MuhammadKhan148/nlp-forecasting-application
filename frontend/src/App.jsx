import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createChart, CrosshairMode } from 'lightweight-charts'
import { fetchHistorical, generateForecast, fetchSymbols, fetchModels, evaluateModels, fetchForecastHistory } from './api'

export default function App() {
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)
  const candleSeriesRef = useRef(null)
  const forecastSeriesRef = useRef(null)
  const actualSeriesRef = useRef(null)
  const pastForecastSeriesRef = useRef(null)
  const metricsBoxRef = useRef(null)

  const [symbols, setSymbols] = useState(['AAPL'])
  const [symbol, setSymbol] = useState('AAPL')
  const [horizon, setHorizon] = useState(24)
  const [model, setModel] = useState('arima')
  const [availableModels, setAvailableModels] = useState({ traditional: [], neural: [] })
  const [metrics, setMetrics] = useState([])
  const [best, setBest] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showActual, setShowActual] = useState(true)
  const [showPast, setShowPast] = useState(true)
  const [actualData, setActualData] = useState([])
  const [pastData, setPastData] = useState([])

  const modelColor = useMemo(() => {
    const palette = {
      arima: '#8b5cf6',
      exp_smooth: '#22c55e',
      ma_5: '#f97316',
      ma_10: '#f59e0b',
      lstm: '#06b6d4',
      gru: '#f43f5e',
    }
    return palette[model] || '#8b5cf6'
  }, [model])

  const horizonLabel = useMemo(() => (horizon === 1 ? '1hr' : `${horizon}hrs`), [horizon])

  // Normalize backend date strings to UTCTimestamp (seconds) for lightweight-charts
  const toUTCTimestamp = (value) => {
    if (!value) return undefined
    if (typeof value === 'number') return Math.floor(value)
    if (typeof value === 'string') {
      // 'YYYY-MM-DD HH:MM' -> 'YYYY-MM-DDTHH:MM:00Z'
      if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(value)) {
        const iso = value.replace(' ', 'T') + ':00Z'
        return Math.floor(new Date(iso).getTime() / 1000)
      }
      // 'YYYY-MM-DD' -> midnight UTC
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const iso = value + 'T00:00:00Z'
        return Math.floor(new Date(iso).getTime() / 1000)
      }
      // Fallback parse
      return Math.floor(new Date(value).getTime() / 1000)
    }
    return undefined
  }

  useEffect(() => {
    fetchSymbols().then((s) => {
      if (s && s.symbols && s.symbols.length) {
        setSymbols(s.symbols)
        if (!s.symbols.includes(symbol)) setSymbol(s.symbols[0])
      }
    }).catch(() => { })
    fetchModels().then(setAvailableModels).catch(() => { })
  }, [])

  useEffect(() => {
    if (!chartContainerRef.current) return
    if (chartRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: { background: { type: 'solid', color: '#0b1220' }, textColor: '#cbd5e1' },
      rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.4)' },
      timeScale: { borderColor: 'rgba(197, 203, 206, 0.4)' },
      crosshair: { mode: CrosshairMode.Normal },
      grid: { vertLines: { color: 'rgba(42, 46, 57, 0.5)' }, horzLines: { color: 'rgba(42, 46, 57, 0.5)' } },
      autoSize: false,
      width: chartContainerRef.current.clientWidth,
      height: 400,
    })

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981', downColor: '#ef4444', wickUpColor: '#10b981', wickDownColor: '#ef4444', borderVisible: false,
    })
    const forecastSeries = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 2 })
    const actualSeries = chart.addLineSeries({ color: '#38bdf8', lineWidth: 1 })
    const pastSeries = chart.addLineSeries({ color: '#f59e0b', lineWidth: 1 })

    chartRef.current = chart
    candleSeriesRef.current = candleSeries
    forecastSeriesRef.current = forecastSeries
    actualSeriesRef.current = actualSeries
    pastForecastSeriesRef.current = pastSeries

    const handleResize = () => chart.applyOptions({ width: chartContainerRef.current.clientWidth })
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Keep chart width in sync with container size to avoid overlap with the metrics panel
  useEffect(() => {
    if (!chartRef.current || !chartContainerRef.current) return
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      const width = Math.floor(entry.contentRect.width)
      if (width > 0) {
        chartRef.current.applyOptions({ width })
      }
    })
    observer.observe(chartContainerRef.current)
    return () => observer.disconnect()
  }, [])

  const loadHistorical = async () => {
    setLoading(true)
    try {
      const data = await fetchHistorical(symbol)
      if (data && data.data && data.data.length) {
        const series = data.data.map(d => ({ time: toUTCTimestamp(d.date), open: d.open, high: d.high, low: d.low, close: d.close }))
        candleSeriesRef.current.setData(series)
        const closes = data.data.map(d => ({ time: toUTCTimestamp(d.date), value: d.close }))
        setActualData(closes)
        if (showActual) {
          actualSeriesRef.current.setData(closes)
        } else {
          actualSeriesRef.current.setData([])
        }
        // Ensure the full dataset is visible after loading
        chartRef.current?.timeScale().fitContent()
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (forecastSeriesRef.current) {
      forecastSeriesRef.current.applyOptions({ color: modelColor })
    }
  }, [modelColor])

  const runForecast = async () => {
    setLoading(true)
    try {
      const resp = await generateForecast(symbol, horizon, model)
      if (resp && resp.forecasts && resp.forecasts.length) {
        const line = resp.forecasts.map(f => ({ time: toUTCTimestamp(f.date), value: (f.predicted_close ?? f.close ?? f.value) }))
        forecastSeriesRef.current.setData(line)
        // Keep everything in view after plotting a forecast
        chartRef.current?.timeScale().fitContent()
      }
    } finally {
      setLoading(false)
    }
  }

  const compareModels = async () => {
    if (!symbol) return
    setLoading(true)
    try {
      const res = await evaluateModels(symbol, 5)
      setMetrics(res.results || [])
      setBest(res.best_model || null)
      // Scroll table into view so users always see the result
      setTimeout(() => { metricsBoxRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }, 50)
    } finally {
      setLoading(false)
    }
  }

  const loadPastForecasts = async () => {
    try {
      const res = await fetchForecastHistory(symbol)
      const rows = res && res.forecasts ? res.forecasts : []
      if (!rows.length) {
        setPastData([])
        pastForecastSeriesRef.current.setData([])
        return
      }
      // Use the latest forecast per forecast_date
      const latestByDate = new Map()
      for (const r of rows) {
        const key = r.forecast_date
        const existing = latestByDate.get(key)
        if (!existing || (r.created_at && r.created_at > existing.created_at)) {
          latestByDate.set(key, r)
        }
      }
      const points = Array.from(latestByDate.values())
        .sort((a, b) => (a.forecast_date < b.forecast_date ? -1 : 1))
        .map(r => ({ time: toUTCTimestamp(r.forecast_date), value: r.predicted_close }))
      setPastData(points)
      if (showPast) {
        pastForecastSeriesRef.current.setData(points)
      } else {
        pastForecastSeriesRef.current.setData([])
      }
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => { loadHistorical(); loadPastForecasts() }, [symbol])

  useEffect(() => {
    if (!actualSeriesRef.current) return
    if (showActual) actualSeriesRef.current.setData(actualData)
    else actualSeriesRef.current.setData([])
  }, [showActual, actualData])

  useEffect(() => {
    if (!pastForecastSeriesRef.current) return
    if (showPast) pastForecastSeriesRef.current.setData(pastData)
    else pastForecastSeriesRef.current.setData([])
  }, [showPast, pastData])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">FinTech Forecasting</div>
        <div className="controls">
          <select value={symbol} onChange={e => setSymbol(e.target.value)}>
            {symbols.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={horizon} onChange={e => setHorizon(parseInt(e.target.value, 10))}>
            <option value="1">1hr</option>
            <option value="3">3hrs</option>
            <option value="24">24hrs</option>
            <option value="72">72hrs</option>
            <option value="120">120hrs</option>
          </select>
          <select value={model} onChange={e => setModel(e.target.value)}>
            {[...availableModels.traditional, ...availableModels.neural].map((m) => (
              <option key={m} value={m}>{m.toUpperCase()}</option>
            ))}
          </select>
          <button onClick={runForecast} disabled={loading}>{loading ? 'Loading...' : 'Generate Forecast'}</button>
          <button onClick={compareModels} disabled={loading}>Compare Models</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>Current model</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#111827', border: '1px solid #1f2937', padding: '4px 8px', borderRadius: 9999 }}>
            <span style={{ width: 10, height: 10, borderRadius: 9999, background: modelColor }} />
            <span style={{ fontWeight: 600, color: '#cbd5e1' }}>{model.toUpperCase()}</span>
          </span>
          <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 8 }}>Horizon</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#111827', border: '1px solid #1f2937', padding: '4px 8px', borderRadius: 9999 }}>
            <span style={{ width: 6, height: 6, borderRadius: 9999, background: '#38bdf8' }} />
            <span style={{ fontWeight: 600, color: '#cbd5e1' }}>{horizonLabel}</span>
          </span>
        </div>
      </header>
      <main className="main">
        <div className="left-col">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: '#94a3b8', fontSize: 12 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 14, background: 'linear-gradient(90deg,#10b981 50%,#ef4444 50%)', borderRadius: 2, border: '1px solid #374151' }} />
              Candlesticks (OHLC)
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 2, background: '#38bdf8', display: 'inline-block' }} />
              Actual Close
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 2, background: modelColor, display: 'inline-block' }} />
              Forecast ({model.toUpperCase()}, {horizonLabel})
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 14, height: 2, background: '#f59e0b', display: 'inline-block' }} />
              Past Forecasts
            </span>
          </div>
          <div ref={chartContainerRef} className="chart" />
        </div>
        <div ref={metricsBoxRef} className="metrics-panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ fontWeight: 600 }}>Model Performance</div>
            <div style={{ display: 'flex', gap: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <input type="checkbox" checked={showActual} onChange={e => setShowActual(e.target.checked)} />
                <span>Show Actual Close</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <input type="checkbox" checked={showPast} onChange={e => setShowPast(e.target.checked)} />
                <span>Show Past Forecasts</span>
              </label>
            </div>
          </div>
          {metrics && metrics.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: 8 }}>Model</th>
                    <th style={{ textAlign: 'left', padding: 8 }}>Type</th>
                    <th style={{ textAlign: 'left', padding: 8 }}>RMSE</th>
                    <th style={{ textAlign: 'left', padding: 8 }}>MAE</th>
                    <th style={{ textAlign: 'left', padding: 8 }}>MAPE</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics
                    .slice()
                    .sort((a, b) => (a.rmse ?? Number.POSITIVE_INFINITY) - (b.rmse ?? Number.POSITIVE_INFINITY))
                    .map((m, i) => (
                      <tr key={i} style={{ background: best && best.model_name === m.model_name ? 'rgba(124,58,237,0.18)' : 'transparent' }}>
                        <td style={{ padding: 8 }}>{m.model_name}</td>
                        <td style={{ padding: 8 }}>{m.model_type}</td>
                        <td style={{ padding: 8 }}>{m.rmse?.toFixed?.(4) ?? '--'}</td>
                        <td style={{ padding: 8 }}>{m.mae?.toFixed?.(4) ?? '--'}</td>
                        <td style={{ padding: 8 }}>{m.mape?.toFixed?.(2) ?? '--'}%</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ color: '#94a3b8' }}>No results yet. Click "Compare Models" to compute metrics.</div>
          )}
        </div>
      </main>
    </div>
  )
}


