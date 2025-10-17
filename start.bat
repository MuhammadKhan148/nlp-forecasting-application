@echo off
REM Quick start script for FinTech Forecasting Application

echo ============================================================
echo   Starting FinTech Forecasting Application...
echo ============================================================
echo.

REM Set MongoDB configuration
set MONGO_URI=mongodb://localhost:27017/nlp
set USE_MONGO=1
set MONGO_DB=nlp

REM Check if database exists
if not exist "database\fintech.db" (
    echo WARNING: Database not found!
    echo Running data loader first...
    python utils\data_loader.py
    echo.
)

echo Starting Flask server...
echo.
echo The application will be available at:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

python run.py

