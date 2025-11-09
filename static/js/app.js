// FinTech Forecasting Application - Enhanced Frontend

let currentSymbol = '';
let historicalData = [];
let forecastData = [];
let errorSeries = [];
let rollingMetrics = {};
let portfolioState = null;

function normalizeForecastEntries(entries) {
    if (!Array.isArray(entries)) {
        return [];
    }
    const normalizedEntries = entries.map((entry) => {
        const normalized = { ...entry };
        const openKey = normalized.predicted_open === undefined ? 'open' : null;
        const highKey = normalized.predicted_high === undefined ? 'high' : null;
        const lowKey = normalized.predicted_low === undefined ? 'low' : null;
        const closeKey = normalized.predicted_close === undefined ? 'close' : null;

        if (openKey && normalized[openKey] !== undefined) {
            normalized.predicted_open = Number(normalized[openKey]);
        }
        if (highKey && normalized[highKey] !== undefined) {
            normalized.predicted_high = Number(normalized[highKey]);
        }
        if (lowKey && normalized[lowKey] !== undefined) {
            normalized.predicted_low = Number(normalized[lowKey]);
        }
        if (closeKey && normalized[closeKey] !== undefined) {
            normalized.predicted_close = Number(normalized[closeKey]);
        }

        // Ensure numeric types
        ['predicted_open', 'predicted_high', 'predicted_low', 'predicted_close', 'confidence_lower', 'confidence_upper', 'horizon_hours', 'step_hours']
            .forEach((key) => {
                if (normalized[key] !== undefined) {
                    const value = Number(normalized[key]);
                    normalized[key] = Number.isNaN(value) ? undefined : value;
                }
            });

        // Derive step_hours if missing
        if (normalized.step_hours === undefined && normalized.horizon_hours !== undefined) {
            const total = Number(normalized.horizon_hours);
            normalized.step_hours = entries.length > 0 ? total / entries.length : total;
        }

        return normalized;
    });

    return normalizedEntries.sort((a, b) => {
        const aTime = new Date(a.date).getTime();
        const bTime = new Date(b.date).getTime();
        if (Number.isNaN(aTime) || Number.isNaN(bTime)) {
            return 0;
        }
        return aTime - bTime;
    });
}

function prettifyModelLabel(rawName) {
    if (!rawName) {
        return 'Unknown';
    }
    const name = String(rawName).trim();
    if (!name) {
        return 'Unknown';
    }

    const normalized = name.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

    if (/^ma[\s_-]*\d+/i.test(normalized)) {
        const window = normalized.match(/\d+/);
        return window ? `Moving Average (${window[0]})` : 'Moving Average';
    }
    if (/^arima/i.test(normalized)) {
        return normalized.toUpperCase();
    }
    if (/^exp/i.test(normalized)) {
        return 'Exponential Smoothing';
    }
    if (/^lstm/i.test(normalized)) {
        return normalized.toUpperCase();
    }
    if (/^gru/i.test(normalized)) {
        return normalized.toUpperCase();
    }

    return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatModelName(details) {
    if (!details) {
        return 'Unknown';
    }
    if (typeof details === 'string') {
        return prettifyModelLabel(details);
    }

    if (details.display_name) {
        return details.display_name;
    }
    if (details.model_name) {
        return prettifyModelLabel(details.model_name);
    }

    const params = details.parameters || {};
    if (params.window) {
        return `Moving Average (${params.window})`;
    }
    if (params.order) {
        const order = Array.isArray(params.order) ? params.order.join(', ') : params.order;
        return `ARIMA (${order})`;
    }
    if (params.trend) {
        return `Exponential Smoothing (${params.trend})`;
    }
    if (params.lookback) {
        const units = params.units ? `, units ${params.units}` : '';
        return `Neural (${params.lookback}-step${units})`;
    }

    return details.model_type === 'neural' ? 'Neural Model' : 'Traditional Model';
}

function formatMetric(value, digits = 4) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '--';
    }
    return Number(value).toFixed(digits);
}

// Initialize application
document.addEventListener('DOMContentLoaded', function () {
    loadModels();
    loadSymbols();
    setupEventListeners();
    updateStatus('Ready', 'success');
});

// Update status indicator
function updateStatus(message, type = 'info') {
    const statusText = document.getElementById('status-text');
    const statusDot = document.querySelector('.status-dot');

    statusText.textContent = message;

    // Update dot color
    statusDot.style.background = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    }[type] || '#94a3b8';
}

// Load available symbols
async function loadSymbols() {
    try {
        const response = await fetch('/api/symbols');
        const data = await response.json();

        const symbolSelect = document.getElementById('symbol-select');
        symbolSelect.innerHTML = '<option value="">-- Select Symbol --</option>';
        currentSymbol = '';

        if (data.symbols && data.symbols.length > 0) {
            data.symbols.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol;
                option.textContent = symbol;
                symbolSelect.appendChild(option);
            });

            // Auto-select first symbol and load data
            if (data.symbols.length > 0) {
                symbolSelect.value = data.symbols[0];
                currentSymbol = data.symbols[0];
                loadHistoricalData(currentSymbol);
            }
        }
    } catch (error) {
        showAlert('Failed to load symbols: ' + error.message, 'error');
        updateStatus('Error loading symbols', 'error');
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        const select = document.getElementById('model-select');
        const hint = document.getElementById('model-hint');

        if (!select) {
            return;
        }

        select.innerHTML = '';

        const addGroup = (label, modelNames) => {
            if (!Array.isArray(modelNames) || modelNames.length === 0) {
                return;
            }
            const group = document.createElement('optgroup');
            group.label = label;
            modelNames.forEach((name) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = prettifyModelLabel(name);
                group.appendChild(option);
            });
            select.appendChild(group);
        };

        addGroup('Traditional Models', data.traditional || []);
        addGroup('Neural Networks', data.neural || []);

        if (select.options.length > 0) {
            select.selectedIndex = 0;
        } else {
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'No models available';
            select.appendChild(placeholder);
        }

        if (hint) {
            if (data.neural && data.neural.length > 0) {
                hint.textContent = 'Neural models powered by TensorFlow; expect longer runtimes.';
            } else {
                hint.textContent = 'Neural models unavailable. Install TensorFlow to enable LSTM/GRU forecasts.';
            }
        }
    } catch (error) {
        showAlert('Failed to load models: ' + error.message, 'error');
        updateStatus('Error loading models', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('symbol-select').addEventListener('change', function (e) {
        currentSymbol = e.target.value;
        if (currentSymbol) {
            loadHistoricalData(currentSymbol);
            document.getElementById('metrics-container').style.display = 'none';
        }
    });

    document.getElementById('forecast-btn').addEventListener('click', generateForecast);
    document.getElementById('evaluate-btn').addEventListener('click', evaluateModels);
    document.getElementById('refresh-btn').addEventListener('click', () => {
        if (currentSymbol) {
            loadHistoricalData(currentSymbol);
        }
    });

    const ingestBtn = document.getElementById('ingest-btn');
    if (ingestBtn) {
        ingestBtn.addEventListener('click', triggerIngestion);
    }

    const trainBtn = document.getElementById('train-btn');
    if (trainBtn) {
        trainBtn.addEventListener('click', triggerTraining);
    }

    const rebalanceBtn = document.getElementById('rebalance-btn');
    if (rebalanceBtn) {
        rebalanceBtn.addEventListener('click', runPortfolioStrategy);
    }
}

// Load historical data
async function loadHistoricalData(symbol) {
    try {
        showLoading(true);
        updateStatus('Loading data...', 'info');

        const response = await fetch(`/api/historical/${symbol}`);
        const result = await response.json();

        if (result.error) {
            showAlert(result.error, 'error');
            updateStatus('Error', 'error');
            return;
        }

        historicalData = result.data;
        renderCandlestickChart(historicalData, [], symbol);
        updateQuickStats(historicalData);
        loadMonitoringData(symbol);
        loadPortfolioSummary();

        showAlert(`Loaded ${result.data.length} days of data for ${symbol}`, 'success');
        updateStatus('Data loaded', 'success');

        showLoading(false);
    } catch (error) {
        showAlert('Failed to load historical data: ' + error.message, 'error');
        updateStatus('Error', 'error');
        showLoading(false);
    }
}

// Generate forecast
async function generateForecast() {
    if (!currentSymbol) {
        showAlert('Please select a symbol first', 'warning');
        return;
    }

    const model = document.getElementById('model-select').value;
    const horizonHours = parseInt(document.getElementById('horizon-select').value);

    try {
        showLoading(true);
        updateStatus('Generating forecast...', 'info');
        document.getElementById('forecast-btn').disabled = true;

        const response = await fetch('/api/forecast', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: currentSymbol,
                model: model,
                horizon_hours: horizonHours
            })
        });

        const result = await response.json();

        if (result.error) {
            showAlert(result.error, 'error');
            updateStatus('Forecast failed', 'error');
            return;
        }

        forecastData = normalizeForecastEntries(result.forecasts);
        const modelLabel = formatModelName(result.model);
        renderCandlestickChart(historicalData, forecastData, currentSymbol, modelLabel);

        const horizonLabel = forecastData.length > 0 && forecastData[forecastData.length - 1].horizon_hours
            ? `${forecastData[forecastData.length - 1].horizon_hours}h`
            : `${horizonHours}h`;
        showAlert(`Forecast generated using ${modelLabel} | Horizon ${horizonLabel}`, 'success');
        loadMonitoringData(currentSymbol);
        loadPortfolioSummary();
        updateStatus(`Forecast ready (${modelLabel})`, 'success');

        showLoading(false);
    } catch (error) {
        showAlert('Failed to generate forecast: ' + error.message, 'error');
        updateStatus('Error', 'error');
    } finally {
        showLoading(false);
        document.getElementById('forecast-btn').disabled = false;
    }
}

// Evaluate models
async function evaluateModels() {
    if (!currentSymbol) {
        showAlert('Please select a symbol first', 'warning');
        return;
    }

    try {
        showLoading(true);
        updateStatus('Evaluating models...', 'info');
        document.getElementById('evaluate-btn').disabled = true;

        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: currentSymbol,
                test_size: 5
            })
        });

        const result = await response.json();

        if (result.error) {
            showAlert(result.error, 'error');
            updateStatus('Evaluation failed', 'error');
            return;
        }

        const metrics = Array.isArray(result.results) ? result.results : [];
        const bestModel = result.best_model || null;
        displayMetrics(metrics, bestModel);

        if (bestModel) {
            const bestName = formatModelName(bestModel);
            const rmse = formatMetric(bestModel.rmse);
            const mae = formatMetric(bestModel.mae);
            showAlert(`Best model for ${currentSymbol}: ${bestName} (RMSE ${rmse}, MAE ${mae})`, 'success');
            updateStatus(`Best model | ${bestName}`, 'success');
        } else {
            showAlert('Model evaluation completed', 'success');
            updateStatus('Evaluation complete', 'success');
        }
        loadMonitoringData(currentSymbol);
    } catch (error) {
        showAlert('Failed to evaluate models: ' + error.message, 'error');
        updateStatus('Error', 'error');
    } finally {
        showLoading(false);
        document.getElementById('evaluate-btn').disabled = false;
    }
}

// Update quick stats
function updateQuickStats(data) {
    if (!data || data.length === 0) {
        document.getElementById('current-price').textContent = '--';
        document.getElementById('price-change').textContent = '--';
        document.getElementById('volume').textContent = '--';
        return;
    }

    const latest = data[data.length - 1];
    const previous = data.length > 1 ? data[data.length - 2] : latest;

    // Current price
    const currentPrice = latest.close;
    document.getElementById('current-price').textContent = `$${currentPrice.toFixed(2)}`;

    // 24h change
    const change = ((currentPrice - previous.close) / previous.close * 100);
    const changeEl = document.getElementById('price-change');
    changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    changeEl.className = `stat-value ${change >= 0 ? 'positive' : 'negative'}`;

    // Volume
    const volume = latest.volume;
    const volumeStr = volume >= 1e6 ? `${(volume / 1e6).toFixed(2)}M` :
        volume >= 1e3 ? `${(volume / 1e3).toFixed(2)}K` :
            volume.toFixed(0);
    document.getElementById('volume').textContent = volumeStr;
}

// Render candlestick chart with Plotly
function renderCandlestickChart(historical, forecast, symbol, modelName = null) {
    const forecastSeries = Array.isArray(forecast) ? forecast : [];
    const traces = [];

    // Historical candlestick
    if (historical && historical.length > 0) {
        traces.push({
            type: 'candlestick',
            x: historical.map(d => d.date),
            open: historical.map(d => d.open),
            high: historical.map(d => d.high),
            low: historical.map(d => d.low),
            close: historical.map(d => d.close),
            name: 'Historical',
            increasing: {
                line: { color: '#22c55e', width: 1.5 },
                fillcolor: '#22c55e'
            },
            decreasing: {
                line: { color: '#ef4444', width: 1.5 },
                fillcolor: '#ef4444'
            },
            whiskerwidth: 0.5,
        });
    }

    // Forecast candlesticks
    if (forecastSeries.length > 0) {
        const getForecastValues = (key) => forecastSeries.map((item) => {
            if (item[key] !== undefined) {
                return item[key];
            }
            const fallback = key.replace('predicted_', '');
            return item[fallback];
        });

        traces.push({
            type: 'candlestick',
            x: forecastSeries.map(d => d.date),
            open: getForecastValues('predicted_open'),
            high: getForecastValues('predicted_high'),
            low: getForecastValues('predicted_low'),
            close: getForecastValues('predicted_close'),
            name: 'Forecast',
            increasing: {
                line: { color: '#8b5cf6', width: 2 },
                fillcolor: 'rgba(139, 92, 246, 0.25)'
            },
            decreasing: {
                line: { color: '#7c3aed', width: 2 },
                fillcolor: 'rgba(124, 58, 237, 0.25)'
            },
            whiskerwidth: 0.8,
        });

        // Add confidence interval
        if (forecastSeries[0].confidence_lower !== undefined) {
            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: forecastSeries.map(d => d.date),
                y: forecastSeries.map(d => d.confidence_upper),
                name: 'Upper Bound',
                line: {
                    color: 'rgba(139, 92, 246, 0.35)',
                    width: 1,
                    dash: 'dot'
                },
                showlegend: false
            });

            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: forecastSeries.map(d => d.date),
                y: forecastSeries.map(d => d.confidence_lower),
                name: 'Confidence Interval',
                fill: 'tonexty',
                fillcolor: 'rgba(139, 92, 246, 0.08)',
                line: {
                    color: 'rgba(139, 92, 246, 0.35)',
                    width: 1,
                    dash: 'dot'
                },
                showlegend: true
            });
        }
    }

    // Update chart title
    const titleEl = document.getElementById('chart-title');
    if (titleEl) {
        const pieces = [`${symbol} Price Chart`];
        if (modelName) {
            pieces.push(`Model: ${modelName}`);
        }
        if (forecastSeries.length > 0) {
            const horizon = forecastSeries[forecastSeries.length - 1].horizon_hours;
            if (horizon) {
                pieces.push(`Horizon: ${horizon}h`);
            }
        }
        titleEl.textContent = pieces.join(' | ');
    }

    const layout = {
        xaxis: {
            title: 'Date',
            rangeslider: { visible: false },
            type: 'date',
            gridcolor: '#232743',
            showgrid: true
        },
        yaxis: {
            title: 'Price (USD)',
            gridcolor: '#232743',
            showgrid: true
        },
        plot_bgcolor: '#141627',
        paper_bgcolor: '#0d1020',
        height: 500,
        margin: { t: 20, b: 50, l: 60, r: 30 },
        showlegend: true,
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'right',
            x: 1,
            bgcolor: 'rgba(13,16,32,0.85)',
            bordercolor: '#232743',
            borderwidth: 1
        },
        hovermode: 'x unified',
        font: {
            family: 'Inter, sans-serif',
            size: 12,
            color: '#e5e7eb'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
        toImageButtonOptions: {
            format: 'png',
            filename: `${symbol}_forecast`,
            height: 600,
            width: 1200,
            scale: 2
        }
    };

    Plotly.newPlot('candlestick-chart', traces, layout, config);
}

// Display model performance metrics
function displayMetrics(results, bestModel = null) {
    const metricsBody = document.getElementById('metrics-body');
    metricsBody.innerHTML = '';

    if (!Array.isArray(results) || results.length === 0) {
        document.getElementById('metrics-container').style.display = 'none';
        const summary = document.getElementById('metrics-summary');
        if (summary) {
            summary.style.display = 'none';
        }
        return;
    }

    // Sort by RMSE (ascending - lower is better)
    results.sort((a, b) => (a.rmse ?? Number.POSITIVE_INFINITY) - (b.rmse ?? Number.POSITIVE_INFINITY));

    results.forEach((result, index) => {
        const row = document.createElement('tr');
        const modelType = result.model_type === 'traditional' ? 'Traditional' : 'Neural';
        const typeClass = result.model_type === 'traditional' ? 'model-traditional' : 'model-neural';
        let isBest = index === 0;
        if (bestModel) {
            const namesMatch = bestModel.model_name && result.model_name && bestModel.model_name === result.model_name;
            const typeMatch = bestModel.model_type && bestModel.model_type === result.model_type;
            const rmseClose = Math.abs((bestModel.rmse ?? 0) - (result.rmse ?? Number.POSITIVE_INFINITY)) < 1e-6;
            isBest = (namesMatch && typeMatch) || rmseClose;
        }

        if (isBest) {
            row.classList.add('best-model');
        }

        row.innerHTML = `
            <td><strong>${formatModelName(result)}</strong></td>
            <td><span class="${typeClass}">${modelType}</span></td>
            <td>${formatMetric(result.rmse)}</td>
            <td>${formatMetric(result.mae)}</td>
            <td>${formatMetric(result.mape, 2)}%</td>
            <td>${result.train_samples ?? '--'}</td>
            <td>${result.test_samples ?? '--'}</td>
        `;

        metricsBody.appendChild(row);
    });

    document.getElementById('metrics-container').style.display = 'block';

    const summaryEl = document.getElementById('metrics-summary');
    if (summaryEl) {
        if (bestModel) {
            summaryEl.textContent = `Best performing model: ${formatModelName(bestModel)} (RMSE ${formatMetric(bestModel.rmse)}, MAE ${formatMetric(bestModel.mae)}, MAPE ${formatMetric(bestModel.mape, 2)}%)`;
            summaryEl.style.display = 'block';
        } else {
            summaryEl.style.display = 'none';
            summaryEl.textContent = '';
        }
    }
}

// Show loading indicator
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Show alert message
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;

    // Add icon
    const icons = {
        success: '[OK]',
        error: '[ERR]',
        warning: '[WARN]',
        info: '[INFO]'
    };

    alert.innerHTML = `<span class="alert-icon">${icons[type] || '[INFO]'}</span> ${message}`;

    const container = document.getElementById('alert-container');
    container.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Monitoring + portfolio helpers
async function loadMonitoringData(symbol) {
    if (!symbol) {
        return;
    }
    const model = document.getElementById('model-select')?.value || 'arima';
    try {
        const [errorsRes, metricsRes] = await Promise.all([
            fetch(`/api/errors/${encodeURIComponent(symbol)}?model=${encodeURIComponent(model)}`),
            fetch(`/api/metrics/rolling/${encodeURIComponent(symbol)}`)
        ]);
        const errorsData = await errorsRes.json();
        const metricsData = await metricsRes.json();
        if (!errorsData.error) {
            errorSeries = errorsData.errors || [];
            renderErrorChart(symbol, errorSeries, model);
        }
        if (!metricsData.error) {
            rollingMetrics = metricsData.metrics || {};
            renderRollingMetrics(rollingMetrics);
        }
    } catch (error) {
        console.warn('Monitoring data failed', error);
    }
}

function renderErrorChart(symbol, series, model) {
    const container = document.getElementById('error-chart');
    if (!container) {
        return;
    }
    if (!Array.isArray(series) || series.length === 0) {
        container.innerHTML = '<p class="muted">No evaluated forecasts yet. Run the adaptive training or wait for new data.</p>';
        return;
    }
    const x = series.map(item => item.forecast_date);
    const y = series.map(item => item.error_pct ?? 0);
    const trace = {
        type: 'bar',
        x,
        y,
        marker: {
            color: y.map(value => value >= 0 ? '#f87171' : '#34d399')
        },
        name: 'Error %'
    };
    const layout = {
        title: `Forecast Error (%) — ${symbol} (${model || 'all models'})`,
        plot_bgcolor: '#141627',
        paper_bgcolor: '#0d1020',
        font: { color: '#e5e7eb' },
        height: 260,
        margin: { t: 40, l: 50, r: 20, b: 50 },
        yaxis: { title: '% Error', gridcolor: '#1f2237' },
        xaxis: { showgrid: false }
    };
    Plotly.newPlot('error-chart', [trace], layout, { displayModeBar: false, responsive: true });
}

function renderRollingMetrics(metrics) {
    document.getElementById('metric-count').textContent = metrics.count ?? 0;
    document.getElementById('metric-rmse').textContent = formatMetric(metrics.rmse);
    document.getElementById('metric-mae').textContent = formatMetric(metrics.mae);
    document.getElementById('metric-mape').textContent = metrics.mape !== undefined && metrics.mape !== null
        ? `${formatMetric(metrics.mape, 2)}%` : '--';
}

async function loadPortfolioSummary() {
    try {
        const response = await fetch('/api/portfolio/summary');
        const result = await response.json();
        if (result.error) {
            return;
        }
        portfolioState = result;
        renderPortfolioSummary(result);
    } catch (error) {
        console.warn('Portfolio summary failed', error);
    }
}

function renderPortfolioSummary(data) {
    if (!data || !data.portfolio) {
        return;
    }
    const portfolio = data.portfolio;
    document.getElementById('portfolio-cash').textContent = `$${Number(portfolio.cash || 0).toFixed(2)}`;
    document.getElementById('portfolio-equity').textContent = `$${Number(data.equity || 0).toFixed(2)}`;
    document.getElementById('portfolio-returns').textContent = `${((data.returns || 0) * 100).toFixed(2)}%`;
    document.getElementById('portfolio-sharpe').textContent = data.sharpe ? data.sharpe.toFixed(2) : '--';

    const positionsBody = document.getElementById('positions-body');
    positionsBody.innerHTML = '';
    (data.positions || []).forEach((pos) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${pos.symbol}</td>
            <td>${Number(pos.quantity).toFixed(4)}</td>
            <td>$${Number(pos.avg_price).toFixed(2)}</td>
        `;
        positionsBody.appendChild(row);
    });
    if ((data.positions || []).length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="3" class="muted">No active positions</td>';
        positionsBody.appendChild(row);
    }

    const tradesBody = document.getElementById('trades-body');
    tradesBody.innerHTML = '';
    (data.trades || []).forEach((trade) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.created_at?.split('T')[0] ?? '--'}</td>
            <td>${trade.symbol}</td>
            <td>${trade.action}</td>
            <td>${Number(trade.quantity).toFixed(4)}</td>
            <td>$${Number(trade.price).toFixed(2)}</td>
        `;
        tradesBody.appendChild(row);
    });
    if ((data.trades || []).length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="muted">No trades executed yet</td>';
        tradesBody.appendChild(row);
    }

    renderPortfolioChart(data.history || []);
}

function renderPortfolioChart(history) {
    const container = document.getElementById('portfolio-equity-chart');
    if (!container) {
        return;
    }
    if (!Array.isArray(history) || history.length === 0) {
        container.innerHTML = '<p class="muted">Run the strategy to generate equity history.</p>';
        return;
    }
    const trace = {
        type: 'scatter',
        mode: 'lines',
        x: history.map(item => item.snapshot_time),
        y: history.map(item => item.equity),
        line: { color: '#34d399', width: 2 },
        name: 'Equity'
    };
    const layout = {
        plot_bgcolor: '#141627',
        paper_bgcolor: '#0d1020',
        font: { color: '#e5e7eb' },
        height: 260,
        margin: { t: 10, l: 50, r: 20, b: 40 },
        yaxis: { title: 'Equity ($)', gridcolor: '#1f2237' },
        xaxis: { showgrid: false }
    };
    Plotly.newPlot('portfolio-equity-chart', [trace], layout, { displayModeBar: false, responsive: true });
}

async function triggerIngestion() {
    const btn = document.getElementById('ingest-btn');
    if (btn) btn.disabled = true;
    try {
        const payload = currentSymbol ? { symbol: currentSymbol } : {};
        const response = await fetch('/api/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.error) {
            showAlert(result.error, 'error');
            return;
        }
        showAlert('Ingestion job triggered', 'success');
        if (currentSymbol) {
            loadHistoricalData(currentSymbol);
        }
    } catch (error) {
        showAlert('Ingestion failed: ' + error.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function triggerTraining() {
    if (!currentSymbol) {
        showAlert('Select a symbol to train', 'warning');
        return;
    }
    const btn = document.getElementById('train-btn');
    if (btn) btn.disabled = true;
    const model = document.getElementById('model-select').value;
    try {
        const response = await fetch('/api/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: currentSymbol,
                model,
                mode: 'update',
                activate: true
            })
        });
        const result = await response.json();
        if (result.error) {
            showAlert(result.error, 'error');
            return;
        }
        showAlert(`Training complete (version ${result.result?.version || 'latest'})`, 'success');
        loadMonitoringData(currentSymbol);
    } catch (error) {
        showAlert('Training failed: ' + error.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function runPortfolioStrategy() {
    const btn = document.getElementById('rebalance-btn');
    if (btn) btn.disabled = true;
    try {
        const response = await fetch('/api/portfolio/run', { method: 'POST' });
        const result = await response.json();
        if (result.error) {
            showAlert(result.error, 'error');
            return;
        }
        showAlert('Portfolio strategy executed', 'success');
        renderPortfolioSummary(result.result || result);
    } catch (error) {
        showAlert('Portfolio update failed: ' + error.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}


