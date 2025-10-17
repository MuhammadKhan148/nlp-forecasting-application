"""
Data loading utilities for importing CSV data into the database.
"""

import sys
import os
import pandas as pd
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database as SqliteDatabase
try:
    from database.mongo_db import MongoDatabase
except Exception:
    MongoDatabase = None


def load_csv_data(csv_path: str, symbol: str, db: Any):
    """
    Load price data from CSV file into database.
    
    Args:
        csv_path: Path to CSV file
        symbol: Symbol name (e.g., AAPL, BTC-USD)
        db: Database instance
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Convert to dictionary records
        records = []
        for _, row in df.iterrows():
            record = {
                'date': str(row['date']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']) if pd.notna(row.get('volume')) else 0,
                'return_1d': float(row['return_1d']) if pd.notna(row.get('return_1d')) else None,
                'vol_5d': float(row['vol_5d']) if pd.notna(row.get('vol_5d')) else None,
                'sma_5': float(row['sma_5']) if pd.notna(row.get('sma_5')) else None,
                'sma_20': float(row['sma_20']) if pd.notna(row.get('sma_20')) else None
            }
            records.append(record)
        
        # Insert into database
        db.insert_historical_data(symbol, records)
        print(f"[OK] Loaded {len(records)} records for {symbol}")
        
    except Exception as e:
        print(f"[ERROR] Error loading {csv_path}: {e}")


def load_sentiment_data(csv_path: str, symbol: str, db: Any):
    """
    Load sentiment data from dataset CSV into database.
    
    Args:
        csv_path: Path to dataset CSV file (contains sentiment columns)
        symbol: Symbol name
        db: Database instance
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Check if sentiment columns exist
        sentiment_cols = ['sent_count', 'sent_mean', 'sent_median', 'sent_std', 
                         'sent_pos_share', 'sent_neg_share']
        
        if not all(col in df.columns for col in sentiment_cols):
            print(f"[SKIP] Sentiment columns not found in {csv_path}")
            return
        
        # Convert to dictionary records
        records = []
        for _, row in df.iterrows():
            record = {
                'date': str(row['date']),
                'sent_count': int(row['sent_count']) if pd.notna(row.get('sent_count')) else 0,
                'sent_mean': float(row['sent_mean']) if pd.notna(row.get('sent_mean')) else 0.0,
                'sent_median': float(row['sent_median']) if pd.notna(row.get('sent_median')) else 0.0,
                'sent_std': float(row['sent_std']) if pd.notna(row.get('sent_std')) else 0.0,
                'sent_pos_share': float(row['sent_pos_share']) if pd.notna(row.get('sent_pos_share')) else 0.0,
                'sent_neg_share': float(row['sent_neg_share']) if pd.notna(row.get('sent_neg_share')) else 0.0
            }
            records.append(record)
        
        # Insert into database
        db.insert_sentiment_data(symbol, records)
        print(f"[OK] Loaded sentiment data for {symbol}")
        
    except Exception as e:
        print(f"[ERROR] Error loading sentiment from {csv_path}: {e}")


def _select_db():
    use_mongo = os.environ.get('USE_MONGO', '0') == '1'
    mongo_uri = os.environ.get('MONGO_URI')
    if use_mongo and mongo_uri and MongoDatabase is not None:
        return MongoDatabase(mongo_uri)
    return SqliteDatabase()


def load_all_data(data_dir: str = None):
    """
    Load all available data from the output directory.
    
    Args:
        data_dir: Optional override directory containing CSV files.
    """
    db = _select_db()
    
    # Resolve data directory candidates relative to this file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_dirs = []
    
    if data_dir:
        candidate_dirs.append(data_dir)
    candidate_dirs.extend(['../output', '../../output', '../../../output'])
    
    data_path = None
    for candidate in candidate_dirs:
        candidate_path = os.path.normpath(os.path.join(script_dir, candidate))
        if os.path.isdir(candidate_path):
            data_path = candidate_path
            break
    
    if data_path is None:
        raise FileNotFoundError(
            f"Could not locate data directory. Checked: {', '.join(candidate_dirs)}"
        )
    
    # List of symbols to load
    symbols = ['AAPL', 'MSFT', 'BTC-USD']
    
    print("=" * 60)
    print("Loading data into database...")
    print("=" * 60)
    print(f"Source directory: {data_path}")
    
    for symbol in symbols:
        print(f"\nProcessing {symbol}...")
        
        # Load price data
        prices_file = os.path.join(data_path, f"prices_{symbol}.csv")
        if os.path.exists(prices_file):
            load_csv_data(prices_file, symbol, db)
        else:
            print(f"[ERROR] Price file not found: {prices_file}")
        
        # Load sentiment data from dataset file
        dataset_file = os.path.join(data_path, f"dataset_{symbol}.csv")
        if os.path.exists(dataset_file):
            load_sentiment_data(dataset_file, symbol, db)
        else:
            print(f"  Note: Dataset file not found: {dataset_file}")
    
    print("\n" + "=" * 60)
    print("Data loading complete!")
    print("=" * 60)
    
    # Print summary
    available_symbols = db.get_available_symbols()
    print(f"\nAvailable symbols in database: {', '.join(available_symbols)}")


if __name__ == "__main__":
    load_all_data()


