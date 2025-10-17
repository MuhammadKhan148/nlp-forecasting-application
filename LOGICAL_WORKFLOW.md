# Logical Workflow - FinTech Forecasting Application

**Student:** Muhammad Abdullah Khan (22i2604)  
**Course:** CS4063 - Natural Language Processing  
**Assignment:** 2 - Stock/Crypto/ForEx Forecasting

---

## 🧠 Application Logic Overview

Your application follows a **predictive analytics pipeline** that transforms historical financial data into future price predictions using machine learning models.

### **Core Logic Flow:**
```
Historical Data → Model Training → Prediction Generation → Visualization → Performance Evaluation
```

---

## 🔄 Step-by-Step Logical Workflow

### **Phase 1: Data Preparation & Model Selection**

#### **Step 1: User Intent Recognition**
**What Happens:**
- User wants to predict future prices for a financial instrument
- User selects: Symbol (AAPL), Model (LSTM), Horizon (24 hours)

**Logic:**
- System validates user selections
- Determines if neural models are available (TensorFlow check)
- Prepares data pipeline for selected symbol

#### **Step 2: Data Retrieval & Validation**
**What Happens:**
- System fetches historical OHLCV data for AAPL
- Validates data quality (no missing values, proper date range)
- Determines if sufficient data exists for model training

**Logic:**
- **Minimum Data Requirement:** At least 100 data points for neural models
- **Data Quality Check:** Remove outliers, handle missing values
- **Time Series Validation:** Ensure chronological order

#### **Step 3: Model Type Decision**
**What Happens:**
- System determines which model to use based on user selection
- Checks model availability and data requirements

**Logic:**
```
IF user_selected_model == "lstm" AND tensorflow_available == True AND data_points >= 100:
    USE LSTM Model
ELIF user_selected_model == "arima":
    USE ARIMA Model
ELIF user_selected_model == "ma_5":
    USE Moving Average (5 periods)
ELSE:
    FALLBACK to ARIMA (most reliable)
```

---

### **Phase 2: Model Training & Learning**

#### **Step 4: Data Preprocessing**
**What Happens:**
- Raw price data is transformed for model consumption
- Different preprocessing for different model types

**Logic:**

**For Neural Models (LSTM/GRU):**
```
1. Normalize data using Z-score: (price - mean) / standard_deviation
2. Create sequences: [t-10, t-9, ..., t-1] → predict t
3. Split data: 90% training, 10% validation
4. Reshape for neural network: (samples, timesteps, features)
```

**For Traditional Models (ARIMA/MA):**
```
1. Check stationarity (if needed, apply differencing)
2. Determine optimal parameters (for ARIMA)
3. Prepare data in time series format
4. No normalization needed (statistical models handle raw prices)
```

#### **Step 5: Model Training**
**What Happens:**
- Model learns patterns from historical data
- Different training strategies for different model types

**Logic:**

**LSTM Training:**
```
1. Initialize neural network with:
   - Input layer: 10 timesteps
   - LSTM layers: 50 → 25 units
   - Dropout: 0.2 (prevent overfitting)
   - Output: 1 unit (predicted price)

2. Training process:
   - Optimizer: Adam
   - Loss function: Mean Squared Error
   - Early stopping: Stop if validation loss doesn't improve for 10 epochs
   - Batch size: 32
   - Maximum epochs: 50

3. Learning objective: Minimize prediction error on validation set
```

**ARIMA Training:**
```
1. Parameter estimation:
   - Auto-regressive order (p): How many past values to use
   - Differencing order (d): How many times to difference data
   - Moving average order (q): How many past errors to use

2. Training process:
   - Maximum likelihood estimation
   - AIC/BIC criteria for model selection
   - Fallback to (1,1,1) if complex model fails

3. Learning objective: Find parameters that best fit historical data
```

#### **Step 6: Model Validation**
**What Happens:**
- Model performance is evaluated on unseen data
- Confidence in predictions is assessed

**Logic:**
```
1. Use last 5 days of data as test set
2. Train on remaining historical data
3. Make predictions on test set
4. Calculate error metrics:
   - RMSE: sqrt(mean((actual - predicted)²))
   - MAE: mean(|actual - predicted|)
   - MAPE: mean(|actual - predicted| / actual) * 100

5. Determine confidence intervals:
   - For LSTM: Based on prediction variance
   - For ARIMA: Based on forecast standard errors
```

---

### **Phase 3: Prediction Generation**

#### **Step 7: Future Prediction**
**What Happens:**
- Model generates predictions for the specified horizon (24 hours)
- Predictions are made recursively for multi-step forecasting

**Logic:**

**LSTM Prediction Process:**
```
1. Start with last 10 known prices
2. For each future timestep:
   a. Feed last 10 prices to LSTM
   b. Get prediction for next timestep
   c. Add prediction to sequence
   d. Remove oldest price, keep sequence length = 10
   e. Repeat for next timestep

3. Denormalize predictions back to original price scale
4. Calculate confidence intervals using prediction uncertainty
```

**ARIMA Prediction Process:**
```
1. Use fitted ARIMA model
2. Call forecast() method with horizon = 24
3. Get point predictions and confidence intervals
4. ARIMA handles multi-step forecasting automatically
```

#### **Step 8: Prediction Post-Processing**
**What Happens:**
- Raw predictions are refined and validated
- Confidence intervals are calculated

**Logic:**
```
1. Validate predictions:
   - Check for unrealistic values (negative prices, extreme jumps)
   - Apply business logic constraints
   - Smooth extreme predictions

2. Calculate confidence intervals:
   - Lower bound: prediction - 1.96 * standard_error
   - Upper bound: prediction + 1.96 * standard_error
   - 95% confidence level

3. Format predictions:
   - Convert to OHLC format (Open, High, Low, Close)
   - Add timestamps for each prediction
   - Include metadata (model used, horizon, confidence)
```

---

### **Phase 4: Visualization & User Experience**

#### **Step 9: Chart Rendering**
**What Happens:**
- Historical data and predictions are displayed on interactive chart
- User can analyze patterns and forecast quality

**Logic:**
```
1. Historical Data Display:
   - Green candlesticks: Close > Open (price went up)
   - Red candlesticks: Close < Open (price went down)
   - Candlestick body: Open to Close range
   - Wicks: High to Low range

2. Forecast Overlay:
   - Purple line extending from last historical point
   - Line represents predicted closing prices
   - Confidence bands shown as shaded area

3. Interactive Features:
   - Zoom: Focus on specific time periods
   - Pan: Navigate through historical data
   - Hover: Show detailed price information
   - Responsive: Adapt to different screen sizes
```

#### **Step 10: User Feedback & Analysis**
**What Happens:**
- User evaluates forecast quality
- System provides performance metrics

**Logic:**
```
1. Visual Analysis:
   - User compares forecast line with historical trends
   - Identifies if forecast seems reasonable
   - Checks confidence intervals for uncertainty

2. Performance Metrics:
   - RMSE: Lower is better (penalizes large errors)
   - MAE: Average error magnitude
   - MAPE: Percentage error (scale-independent)

3. Model Comparison:
   - System can train all models on same data
   - Compare performance metrics
   - Highlight best performing model
```

---

### **Phase 5: Model Comparison & Optimization**

#### **Step 11: Multi-Model Evaluation**
**What Happens:**
- All available models are trained and compared
- Best model is identified for the given data

**Logic:**
```
1. Model Training Loop:
   FOR each available model:
       a. Train model on historical data
       b. Make predictions on test set
       c. Calculate performance metrics
       d. Store results

2. Model Ranking:
   - Primary metric: RMSE (lower is better)
   - Secondary metrics: MAE, MAPE
   - Training time consideration
   - Model complexity vs performance trade-off

3. Best Model Selection:
   - Lowest RMSE wins
   - If RMSE is similar, prefer faster model
   - Consider model interpretability
```

#### **Step 12: Performance Analysis**
**What Happens:**
- System analyzes why certain models perform better
- Provides insights for model selection

**Logic:**
```
1. Performance Analysis:
   - Traditional models: Fast, interpretable, good for stable trends
   - Neural models: Better for complex patterns, slower training
   - Moving Average: Simple baseline, good for noisy data
   - ARIMA: Good for trending data with seasonality
   - Exponential Smoothing: Adaptive to changing trends

2. Model Selection Guidelines:
   - Short-term forecasts: ARIMA or Exponential Smoothing
   - Long-term forecasts: LSTM or GRU
   - Real-time applications: Moving Average (fastest)
   - High accuracy needed: LSTM (if sufficient data)
```

---

## 🎯 Business Logic Summary

### **Core Decision Tree:**
```
1. User selects symbol → Validate data availability
2. User selects model → Check model requirements
3. Data preprocessing → Apply appropriate transformations
4. Model training → Learn patterns from historical data
5. Prediction generation → Forecast future prices
6. Visualization → Display results for user analysis
7. Performance evaluation → Compare model effectiveness
```

### **Key Logic Principles:**

1. **Data Quality First:** Ensure sufficient, clean data before training
2. **Model Appropriateness:** Match model complexity to data characteristics
3. **Fallback Strategy:** Always have a reliable backup model (ARIMA)
4. **User Experience:** Provide clear feedback and performance metrics
5. **Uncertainty Quantification:** Always provide confidence intervals
6. **Performance Optimization:** Balance accuracy with speed

### **Error Handling Logic:**
```
IF insufficient_data:
    SHOW error message, suggest different symbol
ELIF model_training_fails:
    FALLBACK to simpler model
ELIF prediction_fails:
    SHOW error message, retry with different parameters
ELSE:
    DISPLAY results with confidence metrics
```

---

## 🔍 What Each Component Does

### **Frontend Logic:**
- **User Interface:** Captures user intent and preferences
- **Data Visualization:** Transforms numerical predictions into visual insights
- **User Experience:** Provides real-time feedback and error handling

### **Backend Logic:**
- **Data Management:** Ensures data quality and availability
- **Model Orchestration:** Coordinates model training and prediction
- **API Design:** Provides clean interface between frontend and models

### **Model Logic:**
- **Pattern Recognition:** Learns from historical price movements
- **Prediction Generation:** Extrapolates learned patterns into future
- **Uncertainty Quantification:** Provides confidence in predictions

### **Database Logic:**
- **Data Persistence:** Stores historical data and model results
- **Performance Tracking:** Maintains model evaluation history
- **Audit Trail:** Tracks all predictions and their accuracy

---

## 🚀 Why This Logic Works

1. **Modular Design:** Each component has clear responsibility
2. **Robust Fallbacks:** System handles failures gracefully
3. **User-Centric:** Focuses on user needs and experience
4. **Performance-Oriented:** Balances accuracy with speed
5. **Extensible:** Easy to add new models or features
6. **Production-Ready:** Handles real-world scenarios and errors

**This logical workflow ensures your application works reliably and provides valuable insights to users making financial decisions.**
