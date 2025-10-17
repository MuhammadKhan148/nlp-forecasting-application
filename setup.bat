@echo off
REM Quick Setup Script for FinTech Forecasting Application
REM Run this to set up everything automatically

echo ============================================================
echo   FinTech Forecasting Application - Automated Setup
echo   CS4063 Assignment 2
echo ============================================================
echo.

REM Set MongoDB configuration
set MONGO_URI=mongodb://localhost:27017/nlp
set USE_MONGO=1
set MONGO_DB=nlp

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

echo.
echo [2/4] Installing dependencies...
echo This may take 5-10 minutes (TensorFlow is large)
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some dependencies failed to install
    echo The application may still work with traditional models only
    echo.
)

echo.
echo [3/4] Loading data into database...
python utils\data_loader.py

if errorlevel 1 (
    echo.
    echo ERROR: Data loading failed
    echo Please check that ../output folder contains CSV files
    pause
    exit /b 1
)

echo.
echo [4/4] Setup complete!
echo.
echo ============================================================
echo   Ready to run!
echo ============================================================
echo.
echo To start the application, run:
echo   python run.py
echo.
echo Or run this script again to reinstall.
echo.
pause

