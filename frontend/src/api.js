import axios from 'axios'

export async function fetchSymbols() {
  const { data } = await axios.get('/api/symbols')
  return data
}

export async function fetchHistorical(symbol) {
  const { data } = await axios.get(`/api/historical/${encodeURIComponent(symbol)}`)
  return data
}

export async function generateForecast(symbol, horizonHours = 24, model = 'lstm') {
  const { data } = await axios.post('/api/forecast', { symbol, horizon_hours: horizonHours, model })
  return data
}

export async function fetchModels() {
  const { data } = await axios.get('/api/models')
  return data
}

export async function evaluateModels(symbol, testSize = 5) {
  const { data } = await axios.post('/api/evaluate', { symbol, test_size: testSize })
  return data
}

export async function fetchForecastHistory(symbol) {
  const { data } = await axios.get(`/api/forecasts/${encodeURIComponent(symbol)}`)
  return data
}


