// FinTech Forecasting Application - Enhanced Frontend

let currentSymbol = '';
let historicalData = [];
let forecastData = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
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

// Setup event listeners
function setupEventListeners() {
    document.getElementById('symbol-select').addEventListener('change', function(e) {
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
        
        forecastData = result.forecasts;
        renderCandlestickChart(historicalData, forecastData, currentSymbol, result.model);
        
        showAlert(`Forecast generated using ${result.model}`, 'success');
        updateStatus('Forecast ready', 'success');
        
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
        
        displayMetrics(result.results);
        showAlert('Model evaluation completed', 'success');
        updateStatus('Evaluation complete', 'success');
        
        showLoading(false);
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
                line: { color: '#10b981', width: 1.5 },
                fillcolor: '#10b981'
            },
            decreasing: { 
                line: { color: '#ef4444', width: 1.5 },
                fillcolor: '#ef4444'
            },
            whiskerwidth: 0.5,
        });
    }
    
    // Forecast candlesticks
    if (forecast && forecast.length > 0) {
        traces.push({
            type: 'candlestick',
            x: forecast.map(d => d.date),
            open: forecast.map(d => d.predicted_open),
            high: forecast.map(d => d.predicted_high),
            low: forecast.map(d => d.predicted_low),
            close: forecast.map(d => d.predicted_close),
            name: 'Forecast',
            increasing: { 
                line: { color: '#667eea', width: 2 },
                fillcolor: 'rgba(102, 126, 234, 0.3)'
            },
            decreasing: { 
                line: { color: '#764ba2', width: 2 },
                fillcolor: 'rgba(118, 75, 162, 0.3)'
            },
            whiskerwidth: 0.8,
        });
        
        // Add confidence interval
        if (forecast[0].confidence_lower !== undefined) {
            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: forecast.map(d => d.date),
                y: forecast.map(d => d.confidence_upper),
                name: 'Upper Bound',
                line: {
                    color: 'rgba(102, 126, 234, 0.3)',
                    width: 1,
                    dash: 'dot'
                },
                showlegend: false
            });
            
            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: forecast.map(d => d.date),
                y: forecast.map(d => d.confidence_lower),
                name: 'Confidence Interval',
                fill: 'tonexty',
                fillcolor: 'rgba(102, 126, 234, 0.1)',
                line: {
                    color: 'rgba(102, 126, 234, 0.3)',
                    width: 1,
                    dash: 'dot'
                },
                showlegend: true
            });
        }
    }
    
    // Update chart title
    const titleEl = document.getElementById('chart-title');
    if (modelName) {
        titleEl.textContent = `${symbol} - Forecast using ${modelName}`;
    } else {
        titleEl.textContent = `${symbol} - Price Chart`;
    }
    
    const layout = {
        xaxis: {
            title: 'Date',
            rangeslider: { visible: false },
            type: 'date',
            gridcolor: '#e2e8f0',
            showgrid: true
        },
        yaxis: {
            title: 'Price (USD)',
            gridcolor: '#e2e8f0',
            showgrid: true
        },
        plot_bgcolor: '#f8fafc',
        paper_bgcolor: 'white',
        height: 500,
        margin: { t: 20, b: 50, l: 60, r: 30 },
        showlegend: true,
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'right',
            x: 1,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#e2e8f0',
            borderwidth: 1
        },
        hovermode: 'x unified',
        font: {
            family: 'Inter, sans-serif',
            size: 12
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
function displayMetrics(results) {
    const metricsBody = document.getElementById('metrics-body');
    metricsBody.innerHTML = '';
    
    // Sort by RMSE (ascending - lower is better)
    results.sort((a, b) => a.rmse - b.rmse);
    
    results.forEach((result, index) => {
        const row = document.createElement('tr');
        
        // Determine model name
        let modelName = 'Unknown';
        if (result.parameters.window) {
            modelName = `MA-${result.parameters.window}`;
        } else if (result.parameters.order) {
            modelName = `ARIMA (${result.parameters.order.join(',')})`;
        } else if (result.parameters.trend) {
            modelName = `Exp. Smoothing`;
        } else if (result.parameters.lookback) {
            modelName = result.parameters.units === 50 ? 'LSTM-50' : 'GRU-50';
        }
        
        const modelType = result.model_type === 'traditional' ? 'Traditional' : 'Neural';
        const typeClass = result.model_type === 'traditional' ? 'model-traditional' : 'model-neural';
        
        // Highlight best model
        if (index === 0) {
            row.style.background = 'rgba(102, 126, 234, 0.1)';
        }
        
        row.innerHTML = `
            <td><strong>${modelName}</strong></td>
            <td><span class="${typeClass}">${modelType}</span></td>
            <td>${result.rmse.toFixed(4)}</td>
            <td>${result.mae.toFixed(4)}</td>
            <td>${result.mape.toFixed(2)}%</td>
            <td>${result.train_samples}</td>
            <td>${result.test_samples}</td>
        `;
        
        metricsBody.appendChild(row);
    });
    
    document.getElementById('metrics-container').style.display = 'block';
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
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    alert.innerHTML = `<span style="font-size:1.25rem">${icons[type] || 'ℹ'}</span> ${message}`;
    
    const container = document.getElementById('alert-container');
    container.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}
