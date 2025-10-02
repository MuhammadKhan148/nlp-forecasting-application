# Quick Start Guide

Get the FinTech Forecasting Application running in 5 minutes!

## 🚀 Quick Setup (Windows)

### Step 1: Open PowerShell in Project Directory
```powershell
cd assignment2
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

This will take a few minutes (TensorFlow is large). Get a coffee! ☕

### Step 4: Load Data
```powershell
python utils/data_loader.py
```

You should see:
```
============================================================
Loading data into database...
============================================================
✓ Loaded 25 records for AAPL
✓ Loaded 25 records for MSFT
✓ Loaded 25 records for BTC-USD
```

### Step 5: Start the Application
```powershell
python run.py
```

Or directly:
```powershell
python app/app.py
```

### Step 6: Open Your Browser
Navigate to: **http://localhost:5000**

---

## 🎯 Using the Application

1. **Select Symbol:** Choose AAPL, MSFT, or BTC-USD from dropdown
2. **Choose Model:** Pick from:
   - Traditional: MA, ARIMA, Exponential Smoothing
   - Neural: LSTM, GRU
3. **Set Horizon:** 1hr, 3hrs, 24hrs, 72hrs, or 120hrs
4. **Generate Forecast:** Click button and wait 5-30 seconds
5. **View Results:** Interactive candlestick chart appears!

---

## 🧪 Run Tests
```powershell
python tests/test_models.py
```

Expected output:
```
test_all_models_run ... ok
test_evaluate ... ok
test_fit ... ok
test_initialization ... ok
test_predict ... ok

----------------------------------------------------------------------
Ran 15 tests in 12.345s

OK
```

---

## 📊 Model Comparison

Click **"Evaluate Models"** button to compare all models:
- RMSE (lower is better)
- MAE (lower is better)
- MAPE (lower is better)

Results appear in a table below the chart.

---

## 🛠️ Troubleshooting

### "Module not found" Error
```powershell
pip install -r requirements.txt
```

### "Database not found" Error
```powershell
python utils/data_loader.py
```

### TensorFlow Installation Issues
If TensorFlow fails to install:
1. Application still works with traditional models
2. Or try: `pip install tensorflow-cpu==2.15.0`

### Port 5000 Already in Use
Change port in `app/app.py` or `run.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

### No Data in Charts
1. Check browser console (F12) for errors
2. Verify data was loaded: `python utils/data_loader.py`
3. Check database exists: `ls database/fintech.db`

---

## 📁 What Each File Does

- **run.py** - Main entry point with setup checks
- **app/app.py** - Flask server and API endpoints
- **models/traditional_models.py** - MA, ARIMA, Exp. Smoothing
- **models/neural_models.py** - LSTM, GRU
- **database/models.py** - SQLite database interface
- **utils/data_loader.py** - Load CSV data into database
- **templates/index.html** - Web interface
- **static/css/style.css** - Styling
- **static/js/app.js** - Frontend JavaScript

---

## 🎓 For Grading

The application demonstrates:

✅ **Front-end:** Modern web UI with Plotly charts  
✅ **Back-end:** SQLite database with proper schema  
✅ **Traditional Models:** ARIMA, MA, Exp. Smoothing  
✅ **Neural Models:** LSTM, GRU  
✅ **Visualization:** Candlestick charts with forecasts  
✅ **Software Engineering:** Modular code, tests, docs  
✅ **Model Comparison:** Performance metrics table  

---

## 📞 Need Help?

- Check **README.md** for detailed documentation
- Check **REPORT.md** for technical report
- Review code comments for implementation details

---

**Enjoy forecasting! 📈**

