#!/usr/bin/env python3
"""
Main entry point for FinTech Forecasting Application.
This script handles initial setup and starts the Flask server.
"""

import os
import sys
from pathlib import Path

def check_database():
    """Check if database exists and has data."""
    db_path = Path("database/fintech.db")
    
    if not db_path.exists():
        print("\n" + "=" * 60)
        print("⚠️  DATABASE NOT FOUND")
        print("=" * 60)
        print("\nPlease run the data loader first:")
        print("  python utils/data_loader.py")
        print("\nThis will:")
        print("  1. Create the database")
        print("  2. Load historical price data")
        print("  3. Load sentiment data (if available)")
        print("=" * 60)
        
        response = input("\nWould you like to run the data loader now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\nLoading data...")
            from utils.data_loader import load_all_data
            load_all_data()
            print("\n✓ Data loading complete!")
        else:
            print("\nExiting. Please run data loader manually.")
            sys.exit(0)
    else:
        # Check if database has data
        from database.models import Database
        db = Database()
        symbols = db.get_available_symbols()
        
        if not symbols:
            print("\n" + "=" * 60)
            print("⚠️  DATABASE IS EMPTY")
            print("=" * 60)
            print("\nLoading data from CSV files...")
            from utils.data_loader import load_all_data
            load_all_data()
        else:
            print(f"\n✓ Database ready with {len(symbols)} symbols: {', '.join(symbols)}")


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    try:
        import flask
    except ImportError:
        missing.append("flask")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import statsmodels
    except ImportError:
        missing.append("statsmodels")
    
    if missing:
        print("\n" + "=" * 60)
        print("⚠️  MISSING DEPENDENCIES")
        print("=" * 60)
        print("\nThe following packages are required but not installed:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)
    
    # Check optional dependencies
    try:
        import tensorflow
        print("✓ TensorFlow available - Neural models enabled")
    except ImportError:
        print("⚠️  TensorFlow not available - Only traditional models will work")


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  FinTech Forecasting Application")
    print("  CS4063 - Assignment 2")
    print("=" * 60)
    
    # Check dependencies
    print("\nChecking dependencies...")
    check_dependencies()
    
    # Check database
    print("\nChecking database...")
    check_database()
    
    # Start Flask app
    print("\n" + "=" * 60)
    print("Starting Flask server...")
    print("=" * 60)
    print("\n🚀 Application will be available at:")
    print("   http://localhost:5000")
    print("\n📊 Available features:")
    print("   - Select financial instrument (AAPL, MSFT, BTC-USD)")
    print("   - Choose forecasting model (Traditional/Neural)")
    print("   - Set forecast horizon (1hr - 120hrs)")
    print("   - View interactive candlestick charts")
    print("   - Compare model performance")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Import and run Flask app
    from app.app import app
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Server stopped by user")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

