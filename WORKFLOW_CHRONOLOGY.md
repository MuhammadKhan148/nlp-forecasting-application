# Chronological Workflow - FinTech Forecasting Application

**Student:** Muhammad Abdullah Khan (22i2604)  
**Course:** CS4063 - Natural Language Processing  
**Assignment:** 2 - Stock/Crypto/ForEx Forecasting

---

## 🚀 Application Startup Sequence

### **Step 1: Environment Setup**
**Files Involved:**
- `requirements.txt` - Python dependencies
- `frontend/package.json` - React dependencies
- `config.env` - Environment variables

**Process:**
1. Install Python packages: `pip install -r requirements.txt`
2. Install React packages: `cd frontend && npm install`
3. Load environment variables from `config.env`

### **Step 2: Database Initialization**
**Files Involved:**
- `database/models.py` - Database schema
- `utils/data_loader.py` - CSV to database conversion

**Process:**
1. `database/models.py` creates SQLite database with tables:
   - `historical_prices` (OHLCV data)
   - `forecasts` (model predictions)
   - `model_metrics` (performance data)
2. `utils/data_loader.py` loads CSV files into database
3. Database file `fintech.db` is created/updated

### **Step 3: Backend Server Start**
**Files Involved:**
- `app/app.py` - Flask REST API server

**Process:**
1. Flask app initializes on port 5000
2. Database connection established
3. API endpoints registered:
   - `/api/symbols` - Available symbols
   - `/api/historical/{symbol}` - Historical data
   - `/api/models` - Available models
   - `/api/forecast` - Generate predictions
   - `/api/evaluate` - Model comparison

### **Step 4: Frontend Server Start**
**Files Involved:**
- `frontend/vite.config.js` - Vite configuration
- `frontend/src/App.jsx` - React main component

**Process:**
1. Vite dev server starts on port 5173
2. React app loads with dark theme
3. Proxy configured to route `/api/*` to Flask backend

---

## 🔄 User Interaction Workflow

### **Phase 1: Initial Page Load**

#### **Step 1: React App Initialization**
**Files Involved:**
- `frontend/src/App.jsx` (lines 1-50)
- `frontend/src/styles.css` (lines 1-100)

**Process:**
1. React component mounts
2. State variables initialized:
   - `symbols: []` - Available symbols
   - `selectedSymbol: 'AAPL'` - Default symbol
   - `forecastHorizon: 24` - Default horizon
   - `selectedModel: 'arima'` - Default model
3. Dark theme CSS applied
4. UI components rendered

#### **Step 2: Load Available Symbols**
**Files Involved:**
- `frontend/src/api.js` (lines 1-20)
- `app/app.py` (lines 50-60)

**Process:**
1. `fetchSymbols()` called from `api.js`
2. HTTP GET request to `/api/symbols`
3. Flask returns `{"symbols": ["AAPL", "MSFT", "BTC-USD"]}`
4. React state updated with symbol list
5. Dropdown populated with symbols

#### **Step 3: Load Available Models**
**Files Involved:**
- `frontend/src/api.js` (lines 21-40)
- `app/app.py` (lines 200-220)

**Process:**
1. `fetchModels()` called from `api.js`
2. HTTP GET request to `/api/models`
3. Flask checks model availability:
   - Traditional: `["arima", "ma_5", "ma_10", "exp_smooth"]`
   - Neural: `["lstm", "gru"]` (if TensorFlow available)
4. React state updated with model list
5. Model dropdown populated

#### **Step 4: Load Historical Data**
**Files Involved:**
- `frontend/src/api.js` (lines 41-60)
- `app/app.py` (lines 80-120)
- `database/models.py` (lines 50-80)

**Process:**
1. `fetchHistoricalData('AAPL')` called automatically
2. HTTP GET request to `/api/historical/AAPL`
3. Flask queries database: `SELECT * FROM historical_prices WHERE symbol='AAPL'`
4. Database returns OHLCV data
5. Flask formats response with timestamps
6. React receives data and updates chart

### **Phase 2: Chart Rendering**

#### **Step 5: Initialize Candlestick Chart**
**Files Involved:**
- `frontend/src/App.jsx` (lines 100-150)
- `frontend/src/styles.css` (lines 200-300)

**Process:**
1. `useEffect` hook triggers on data load
2. Lightweight Charts library initialized
3. Candlestick series created with historical data
4. Chart configured with dark theme:
   - Background: `#0f0f0f`
   - Grid: `#2a2a2a`
   - Candles: Green/red based on close > open
5. Chart rendered in DOM

### **Phase 3: User Interaction**

#### **Step 6: User Selects Different Symbol**
**Files Involved:**
- `frontend/src/App.jsx` (lines 200-250)

**Process:**
1. User clicks symbol dropdown
2. `handleSymbolChange()` function called
3. New symbol selected (e.g., 'MSFT')
4. `fetchHistoricalData('MSFT')` called automatically
5. Chart updates with new data
6. Loading indicator shown during fetch

#### **Step 7: User Selects Model**
**Files Involved:**
- `frontend/src/App.jsx` (lines 250-300)

**Process:**
1. User clicks model dropdown
2. `handleModelChange()` function called
3. New model selected (e.g., 'lstm')
4. Model state updated
5. UI reflects selection

#### **Step 8: User Sets Forecast Horizon**
**Files Involved:**
- `frontend/src/App.jsx` (lines 300-350)

**Process:**
1. User clicks horizon dropdown
2. `handleHorizonChange()` function called
3. New horizon selected (e.g., 72 hours)
4. Horizon state updated
5. UI reflects selection

### **Phase 4: Forecast Generation**

#### **Step 9: User Clicks "Generate Forecast"**
**Files Involved:**
- `frontend/src/App.jsx` (lines 400-450)
- `frontend/src/api.js` (lines 80-120)
- `app/app.py` (lines 150-200)

**Process:**
1. User clicks forecast button
2. `handleGenerateForecast()` called
3. Loading state set to true
4. `generateForecast()` API call made with:
   - Symbol: 'MSFT'
   - Model: 'lstm'
   - Horizon: 72
5. HTTP POST to `/api/forecast`
6. Flask receives request and validates parameters

#### **Step 10: Model Training & Prediction**
**Files Involved:**
- `app/app.py` (lines 150-200)
- `models/neural_models.py` (lines 1-100)
- `models/traditional_models.py` (lines 1-100)

**Process:**
1. Flask determines model type (neural vs traditional)
2. Model class instantiated:
   - `LSTMModel()` for LSTM
   - `ARIMAModel()` for ARIMA
   - etc.
3. Historical data retrieved from database
4. Model training:
   - **LSTM**: Data normalized, sequences created, model.fit()
   - **ARIMA**: statsmodels ARIMA.fit()
5. Prediction generated:
   - **LSTM**: Recursive prediction for 72 hours
   - **ARIMA**: forecast() method called
6. Confidence intervals calculated
7. Results formatted and returned

#### **Step 11: Forecast Display**
**Files Involved:**
- `frontend/src/App.jsx` (lines 450-500)

**Process:**
1. API response received with forecast data
2. Forecast line series added to chart
3. Purple line extends from historical data
4. Loading state set to false
5. Success message displayed
6. Chart shows both historical and predicted data

### **Phase 5: Model Comparison**

#### **Step 12: User Clicks "Compare Models"**
**Files Involved:**
- `frontend/src/App.jsx` (lines 500-550)
- `frontend/src/api.js` (lines 120-160)
- `app/app.py` (lines 250-300)

**Process:**
1. User clicks compare button
2. `handleCompareModels()` called
3. Loading state set to true
4. `evaluateModels()` API call made
5. HTTP POST to `/api/evaluate`
6. Flask receives request

#### **Step 13: Model Evaluation**
**Files Involved:**
- `app/app.py` (lines 250-300)
- `models/traditional_models.py` (lines 100-200)
- `models/neural_models.py` (lines 100-200)
- `database/models.py` (lines 100-150)

**Process:**
1. Flask loads all available models
2. For each model:
   - Historical data retrieved
   - Model trained on training set
   - Predictions made on test set
   - Metrics calculated (RMSE, MAE, MAPE)
   - Results saved to database
3. All results compiled and returned
4. Best model identified (lowest RMSE)

#### **Step 14: Results Display**
**Files Involved:**
- `frontend/src/App.jsx` (lines 550-600)

**Process:**
1. API response received with all model metrics
2. Performance table populated
3. Best model highlighted (green background)
4. Loading state set to false
5. Table shows:
   - Model name
   - RMSE, MAE, MAPE
   - Training time
   - Model type

---

## 🔄 Data Flow Summary

### **Frontend → Backend Flow**
```
React Component → API Call → Flask Endpoint → Database Query → Model Training → Response
```

### **File Dependencies**
```
frontend/src/App.jsx
    ↓ (API calls)
frontend/src/api.js
    ↓ (HTTP requests)
app/app.py
    ↓ (database queries)
database/models.py
    ↓ (model instantiation)
models/traditional_models.py
models/neural_models.py
```

### **State Management Flow**
```
User Interaction → React State Update → API Call → Backend Processing → Database Update → Response → UI Update
```

---

## 📊 Performance Timeline

### **Typical Response Times**
- **Symbol Change**: 200-500ms (database query)
- **Model Selection**: <50ms (state update)
- **Forecast Generation**: 2-30s (depending on model)
- **Model Comparison**: 10-60s (all models trained)

### **Resource Usage**
- **Memory**: ~100MB (Flask) + ~50MB (React)
- **CPU**: High during model training, low during UI interaction
- **Storage**: ~10MB (SQLite database)

---

## 🎯 Key File Responsibilities

| File | Primary Responsibility | Key Functions |
|------|----------------------|---------------|
| `frontend/src/App.jsx` | React UI state management | `handleSymbolChange()`, `handleGenerateForecast()` |
| `frontend/src/api.js` | HTTP API communication | `fetchSymbols()`, `generateForecast()`, `evaluateModels()` |
| `app/app.py` | Flask REST API server | `/api/symbols`, `/api/forecast`, `/api/evaluate` |
| `database/models.py` | Database operations | `get_historical_data()`, `insert_forecast()`, `save_model_metrics()` |
| `models/traditional_models.py` | Statistical models | `ARIMAModel`, `MovingAverageModel`, `ExponentialSmoothingModel` |
| `models/neural_models.py` | Deep learning models | `LSTMModel`, `GRUModel` |
| `frontend/src/styles.css` | Dark theme styling | Chart colors, component styling |
| `utils/data_loader.py` | Data initialization | CSV to database conversion |

---

## 🚨 Error Handling Flow

### **Frontend Errors**
1. **Network Error**: `api.js` catches HTTP errors, shows user message
2. **Invalid Data**: `App.jsx` validates responses, shows error state
3. **Chart Error**: Lightweight Charts handles rendering errors gracefully

### **Backend Errors**
1. **Model Training Error**: `app.py` catches exceptions, falls back to simpler model
2. **Database Error**: `models.py` handles connection issues, returns empty results
3. **Validation Error**: `app.py` validates input parameters, returns 400 error

---

## 🔧 Development Workflow

### **Code Changes**
1. **Frontend**: Edit `frontend/src/App.jsx` → Vite hot reload → Instant UI update
2. **Backend**: Edit `app/app.py` → Restart Flask → API changes active
3. **Models**: Edit `models/*.py` → Restart Flask → New model behavior
4. **Styling**: Edit `frontend/src/styles.css` → Vite hot reload → Instant style update

### **Testing Workflow**
1. **Unit Tests**: `python -m unittest tests/test_models.py`
2. **Integration Tests**: Manual API testing via browser
3. **UI Tests**: Manual interaction testing in React app

---

**This chronological workflow shows exactly how your application works from startup to user interaction, with specific file references for each step.**
