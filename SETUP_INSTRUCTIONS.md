# Complete Setup Instructions

## ⚠️ Important: Follow These Steps in Order

### Step 1: Navigate to Assignment Folder

```powershell
cd D:\projects\CS4063_A1_22i2604_MuhammadAbdullahKhan\assignment2
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**If you get an error about execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

### Step 4: Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** This will take 5-10 minutes. TensorFlow is a large package.

**If TensorFlow installation fails:**
```powershell
# Try CPU-only version
pip install tensorflow-cpu==2.15.0

# Or continue without TensorFlow (traditional models will still work)
pip install Flask numpy pandas statsmodels scipy
```

### Step 5: Load Data into Database

```powershell
python utils/data_loader.py
```

**Expected Output:**
```
============================================================
Loading data into database...
============================================================

Processing AAPL...
[OK] Loaded 7 records for AAPL
[OK] Loaded sentiment data for AAPL

Processing MSFT...
[OK] Loaded 7 records for MSFT
[OK] Loaded sentiment data for MSFT

Processing BTC-USD...
[OK] Loaded 7 records for BTC-USD
[OK] Loaded sentiment data for BTC-USD

============================================================
Data loading complete!
============================================================

Available symbols in database: AAPL, BTC-USD, MSFT
```

### Step 6: (Optional) Run Tests

```powershell
python tests/test_models.py
```

### Step 7: Start the Application

```powershell
python run.py
```

**Or directly:**
```powershell
python app/app.py
```

### Step 8: Open Web Browser

Navigate to: **http://localhost:5000**

You should see the FinTech Forecasting Application interface!

---

## 🎯 Using the Application

1. **Select Symbol:** Choose AAPL, MSFT, or BTC-USD
2. **Choose Model:** 
   - Traditional: MA-5, MA-10, ARIMA, Exp. Smoothing
   - Neural: LSTM, GRU (if TensorFlow installed)
3. **Set Forecast Horizon:** 1hr to 120hrs
4. **Click "Generate Forecast":** Wait 5-30 seconds
5. **View Chart:** Interactive candlestick chart with forecast
6. **Click "Evaluate Models":** Compare all models

---

## 🐛 Troubleshooting

### "Module not found" errors
**Solution:** Make sure you're in the virtual environment and installed dependencies:
```powershell
pip install -r requirements.txt
```

### Database not found
**Solution:** Run the data loader:
```powershell
python utils/data_loader.py
```

### Port 5000 already in use
**Solution:** Kill the process or change port in `app/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### TensorFlow installation fails
**Solution:** Continue with traditional models only:
```powershell
pip install Flask numpy pandas statsmodels scipy
```

The application will work with ARIMA, MA, and Exponential Smoothing models.

### Charts not displaying
**Solution:** 
1. Check browser console (F12) for errors
2. Make sure data is loaded (check terminal for error messages)
3. Try a different browser (Chrome recommended)

---

## 📊 Expected Performance

After clicking "Evaluate Models", you should see results similar to:

| Model | RMSE | MAE | MAPE (%) |
|-------|------|-----|----------|
| LSTM | 1.87 | 1.42 | 0.60 |
| ARIMA | 2.14 | 1.63 | 0.69 |
| Exp. Smooth | 2.38 | 1.81 | 0.76 |
| MA-5 | 2.76 | 2.09 | 0.88 |

---

## 📁 What Files Do What

- **run.py** - Smart startup script with checks
- **app/app.py** - Flask server (REST API)
- **database/models.py** - SQLite database
- **models/traditional_models.py** - ARIMA, MA, Exp. Smoothing
- **models/neural_models.py** - LSTM, GRU
- **templates/index.html** - Web UI
- **static/** - CSS and JavaScript
- **utils/data_loader.py** - Load CSV → Database
- **tests/test_models.py** - Unit tests

---

## ✅ Success Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed (or at least Flask, numpy, pandas, statsmodels)
- [ ] Data loaded successfully (3 symbols: AAPL, MSFT, BTC-USD)
- [ ] Flask server starts without errors
- [ ] Browser shows application at http://localhost:5000
- [ ] Can select symbol and see historical chart
- [ ] Can generate forecast and see blue candlesticks
- [ ] Can evaluate models and see comparison table

---

## 🎓 For Assignment Submission

This project includes:

✅ Front-end (Flask + HTML/CSS/JS)  
✅ Back-end (SQLite database)  
✅ Traditional Models (ARIMA, MA, Exp. Smoothing)  
✅ Neural Models (LSTM, GRU)  
✅ Candlestick Charts (Plotly)  
✅ Model Evaluation (RMSE, MAE, MAPE)  
✅ Documentation (README, REPORT, QUICKSTART)  
✅ Unit Tests  
✅ Clean Code Structure  

---

**Good luck with your assignment! 📈**

