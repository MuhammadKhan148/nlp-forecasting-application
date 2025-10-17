"""
Database models for the FinTech forecasting application.
Uses SQLite for simplicity and portability.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import os


class Database:
    """Database manager for financial data and forecasts."""
    
    def __init__(self, db_path: str = "database/fintech.db"):
        """Initialize database connection."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_schema()
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def init_schema(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table for historical price data (OHLCV)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER,
                return_1d REAL,
                vol_5d REAL,
                sma_5 REAL,
                sma_20 REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # Table for sentiment data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                sent_count INTEGER,
                sent_mean REAL,
                sent_median REAL,
                sent_std REAL,
                sent_pos_share REAL,
                sent_neg_share REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # Table for forecasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                model_name TEXT NOT NULL,
                forecast_date DATE NOT NULL,
                horizon_hours INTEGER NOT NULL,
                predicted_open REAL,
                predicted_high REAL,
                predicted_low REAL,
                predicted_close REAL,
                confidence_lower REAL,
                confidence_upper REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, model_name, forecast_date, horizon_hours)
            )
        """)
        
        # Table for model performance metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                model_name TEXT NOT NULL,
                rmse REAL,
                mae REAL,
                mape REAL,
                train_samples INTEGER,
                test_samples INTEGER,
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert_historical_data(self, symbol: str, data: List[Dict[str, Any]]):
        """Insert historical price data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for row in data:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_prices 
                    (symbol, date, open, high, low, close, volume, return_1d, vol_5d, sma_5, sma_20)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    row['date'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row.get('volume', 0),
                    row.get('return_1d'),
                    row.get('vol_5d'),
                    row.get('sma_5'),
                    row.get('sma_20')
                ))
            except Exception as e:
                print(f"Error inserting row: {e}")
                continue
        
        conn.commit()
        conn.close()
    
    def insert_sentiment_data(self, symbol: str, data: List[Dict[str, Any]]):
        """Insert sentiment data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for row in data:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO sentiment_data 
                    (symbol, date, sent_count, sent_mean, sent_median, sent_std, sent_pos_share, sent_neg_share)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    row['date'],
                    row.get('sent_count', 0),
                    row.get('sent_mean', 0),
                    row.get('sent_median', 0),
                    row.get('sent_std', 0),
                    row.get('sent_pos_share', 0),
                    row.get('sent_neg_share', 0)
                ))
            except Exception as e:
                print(f"Error inserting sentiment row: {e}")
                continue
        
        conn.commit()
        conn.close()
    
    def get_historical_data(self, symbol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve historical price data for a symbol."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT date, open, high, low, close, volume, return_1d, vol_5d, sma_5, sma_20
            FROM historical_prices
            WHERE symbol = ?
            ORDER BY date ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (symbol,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'volume': row[5],
                'return_1d': row[6],
                'vol_5d': row[7],
                'sma_5': row[8],
                'sma_20': row[9]
            }
            for row in rows
        ]
    
    def insert_forecast(self, symbol: str, model_name: str, forecast_date: str, 
                       horizon_hours: int, predictions: Dict[str, float]):
        """Insert forecast data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO forecasts 
                (symbol, model_name, forecast_date, horizon_hours, 
                 predicted_open, predicted_high, predicted_low, predicted_close,
                 confidence_lower, confidence_upper)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                model_name,
                forecast_date,
                horizon_hours,
                predictions.get('predicted_open') or predictions.get('open'),
                predictions.get('predicted_high') or predictions.get('high'),
                predictions.get('predicted_low') or predictions.get('low'),
                predictions.get('predicted_close') or predictions.get('close'),
                predictions.get('confidence_lower'),
                predictions.get('confidence_upper')
            ))
            conn.commit()
        except Exception as e:
            print(f"Error inserting forecast: {e}")
        finally:
            conn.close()
    
    def get_forecasts(self, symbol: str, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve forecasts for a symbol."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if model_name:
            cursor.execute("""
                SELECT model_name, forecast_date, horizon_hours, 
                       predicted_open, predicted_high, predicted_low, predicted_close,
                       confidence_lower, confidence_upper, created_at
                FROM forecasts
                WHERE symbol = ? AND model_name = ?
                ORDER BY forecast_date ASC
            """, (symbol, model_name))
        else:
            cursor.execute("""
                SELECT model_name, forecast_date, horizon_hours, 
                       predicted_open, predicted_high, predicted_low, predicted_close,
                       confidence_lower, confidence_upper, created_at
                FROM forecasts
                WHERE symbol = ?
                ORDER BY forecast_date ASC
            """, (symbol,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'model_name': row[0],
                'forecast_date': row[1],
                'horizon_hours': row[2],
                'predicted_open': row[3],
                'predicted_high': row[4],
                'predicted_low': row[5],
                'predicted_close': row[6],
                'confidence_lower': row[7],
                'confidence_upper': row[8],
                'created_at': row[9]
            }
            for row in rows
        ]
    
    def save_model_metrics(self, symbol: str, model_name: str, metrics: Dict[str, Any]):
        """Save or update model performance metrics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO model_metrics 
                (symbol, model_name, rmse, mae, mape, train_samples, test_samples, parameters, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                symbol,
                model_name,
                metrics.get('rmse'),
                metrics.get('mae'),
                metrics.get('mape'),
                metrics.get('train_samples'),
                metrics.get('test_samples'),
                json.dumps(metrics.get('parameters', {}))
            ))
            conn.commit()
        except Exception as e:
            print(f"Error saving model metrics: {e}")
        finally:
            conn.close()
    
    def get_model_metrics(self, symbol: str) -> List[Dict[str, Any]]:
        """Retrieve model performance metrics for a symbol."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT model_name, rmse, mae, mape, train_samples, test_samples, parameters, updated_at
            FROM model_metrics
            WHERE symbol = ?
            ORDER BY updated_at DESC
        """, (symbol,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'model_name': row[0],
                'rmse': row[1],
                'mae': row[2],
                'mape': row[3],
                'train_samples': row[4],
                'test_samples': row[5],
                'parameters': json.loads(row[6]) if row[6] else {},
                'updated_at': row[7]
            }
            for row in rows
        ]
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT symbol FROM historical_prices ORDER BY symbol
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]

