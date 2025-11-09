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

        def ensure_column(table: str, column: str, definition: str):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

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

        # Extend forecasts table with evaluation columns
        ensure_column("forecasts", "model_version", "TEXT")
        ensure_column("forecasts", "actual_close", "REAL")
        ensure_column("forecasts", "error_abs", "REAL")
        ensure_column("forecasts", "error_pct", "REAL")
        ensure_column("forecasts", "evaluated_at", "TIMESTAMP")

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

        # Table for detailed metrics history (continuous evaluation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                model_name TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                rmse REAL,
                mae REAL,
                mape REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Model registry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                train_start TEXT,
                train_end TEXT,
                metrics TEXT,
                hyperparams TEXT,
                artifact_path TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, model_name, version)
            )
        """)

        # Ingestion events log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                source TEXT,
                rows_inserted INTEGER,
                status TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Portfolio tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                strategy TEXT,
                cash REAL DEFAULT 0,
                initial_cash REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(portfolio_id, symbol),
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_equity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                holdings_value REAL NOT NULL,
                returns REAL,
                volatility REAL,
                sharpe REAL,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
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
                (symbol, model_name, model_version, forecast_date, horizon_hours, 
                 predicted_open, predicted_high, predicted_low, predicted_close,
                 confidence_lower, confidence_upper)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                model_name,
                predictions.get('model_version'),
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

    # ------------------------------------------------------------------
    # New helpers for assignment 3
    # ------------------------------------------------------------------

    def insert_ingestion_event(self, symbol: str, source: str, rows_inserted: int,
                               status: str, message: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ingestion_events (symbol, source, rows_inserted, status, message)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, source, rows_inserted, status, message))
        conn.commit()
        conn.close()

    def insert_model_version(self, symbol: str, model_name: str, version: str,
                             status: str, train_start: str, train_end: str,
                             metrics: Dict[str, Any], hyperparams: Dict[str, Any],
                             artifact_path: str, activate: bool = False):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO model_versions
            (symbol, model_name, version, status, train_start, train_end, metrics,
             hyperparams, artifact_path, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            symbol,
            model_name,
            version,
            status,
            train_start,
            train_end,
            json.dumps(metrics or {}),
            json.dumps(hyperparams or {}),
            artifact_path,
            1 if activate else 0
        ))
        conn.commit()
        conn.close()
        if activate:
            self.set_active_model_version(symbol, model_name, version)

    def set_active_model_version(self, symbol: str, model_name: str, version: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE model_versions
            SET is_active = CASE WHEN version = ? THEN 1 ELSE 0 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ? AND model_name = ?
        """, (version, symbol, model_name))
        conn.commit()
        conn.close()

    def get_model_versions(self, symbol: str, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if model_name:
            cursor.execute("""
                SELECT symbol, model_name, version, status, train_start, train_end,
                       metrics, hyperparams, artifact_path, is_active, created_at, updated_at
                FROM model_versions
                WHERE symbol = ? AND model_name = ?
                ORDER BY created_at DESC
            """, (symbol, model_name))
        else:
            cursor.execute("""
                SELECT symbol, model_name, version, status, train_start, train_end,
                       metrics, hyperparams, artifact_path, is_active, created_at, updated_at
                FROM model_versions
                WHERE symbol = ?
                ORDER BY created_at DESC
            """, (symbol,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'symbol': row[0],
                'model_name': row[1],
                'version': row[2],
                'status': row[3],
                'train_start': row[4],
                'train_end': row[5],
                'metrics': json.loads(row[6]) if row[6] else {},
                'hyperparams': json.loads(row[7]) if row[7] else {},
                'artifact_path': row[8],
                'is_active': bool(row[9]),
                'created_at': row[10],
                'updated_at': row[11]
            }
            for row in rows
        ]

    def get_active_model_version(self, symbol: str, model_name: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, model_name, version, status, train_start, train_end,
                   metrics, hyperparams, artifact_path, is_active, created_at, updated_at
            FROM model_versions
            WHERE symbol = ? AND model_name = ? AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
        """, (symbol, model_name))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'symbol': row[0],
            'model_name': row[1],
            'version': row[2],
            'status': row[3],
            'train_start': row[4],
            'train_end': row[5],
            'metrics': json.loads(row[6]) if row[6] else {},
            'hyperparams': json.loads(row[7]) if row[7] else {},
            'artifact_path': row[8],
            'is_active': bool(row[9]),
            'created_at': row[10],
            'updated_at': row[11]
        }

    def get_pending_forecasts(self, min_age_minutes: int = 60) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, symbol, model_name, model_version, forecast_date, horizon_hours,
                   predicted_open, predicted_high, predicted_low, predicted_close,
                   created_at
            FROM forecasts
            WHERE actual_close IS NULL
              AND datetime(created_at) <= datetime('now', '-{min_age_minutes} minutes')
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'symbol': row[1],
                'model_name': row[2],
                'model_version': row[3],
                'forecast_date': row[4],
                'horizon_hours': row[5],
                'predicted_open': row[6],
                'predicted_high': row[7],
                'predicted_low': row[8],
                'predicted_close': row[9],
                'created_at': row[10]
            }
            for row in rows
        ]

    def update_forecast_evaluation(self, forecast_id: int, actual_close: float,
                                   error_abs: float, error_pct: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE forecasts
            SET actual_close = ?, error_abs = ?, error_pct = ?, evaluated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_close, error_abs, error_pct, forecast_id))
        conn.commit()
        conn.close()

    def insert_metrics_history(self, symbol: str, model_name: str, horizon_hours: int,
                               rmse: float, mae: float, mape: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics_history (symbol, model_name, horizon_hours, rmse, mae, mape)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (symbol, model_name, horizon_hours, rmse, mae, mape))
        conn.commit()
        conn.close()

    def get_metrics_history(self, symbol: str, limit_days: int = 30) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, model_name, horizon_hours, rmse, mae, mape, created_at
            FROM metrics_history
            WHERE symbol = ? AND datetime(created_at) >= datetime('now', ?)
            ORDER BY created_at DESC
        """, (symbol, f"-{limit_days} days"))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'symbol': row[0],
                'model_name': row[1],
                'horizon_hours': row[2],
                'rmse': row[3],
                'mae': row[4],
                'mape': row[5],
                'created_at': row[6]
            }
            for row in rows
        ]

    def get_forecast_errors(self, symbol: str, model_name: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if model_name:
            cursor.execute("""
                SELECT forecast_date, model_name, model_version, horizon_hours,
                       predicted_close, actual_close, error_abs, error_pct
                FROM forecasts
                WHERE symbol = ? AND model_name = ? AND actual_close IS NOT NULL
                ORDER BY forecast_date DESC
                LIMIT ?
            """, (symbol, model_name, limit))
        else:
            cursor.execute("""
                SELECT forecast_date, model_name, model_version, horizon_hours,
                       predicted_close, actual_close, error_abs, error_pct
                FROM forecasts
                WHERE symbol = ? AND actual_close IS NOT NULL
                ORDER BY forecast_date DESC
                LIMIT ?
            """, (symbol, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'forecast_date': row[0],
                'model_name': row[1],
                'horizon_hours': row[3],
                'predicted_close': row[4],
                'actual_close': row[5],
                'error_abs': row[6],
                'error_pct': row[7],
                'model_version': row[2]
            }
            for row in rows
        ]

    def get_price_for_date(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, open, high, low, close, volume
            FROM historical_prices
            WHERE symbol = ? AND date = ?
            LIMIT 1
        """, (symbol, date))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'date': row[0],
            'open': row[1],
            'high': row[2],
            'low': row[3],
            'close': row[4],
            'volume': row[5]
        }

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, close
            FROM historical_prices
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
        """, (symbol,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {'date': row[0], 'close': row[1]}

    def get_latest_forecast(self, symbol: str, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if model_name:
            cursor.execute("""
                SELECT forecast_date, model_name, model_version, horizon_hours, predicted_close, confidence_lower, confidence_upper
                FROM forecasts
                WHERE symbol = ? AND model_name = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (symbol, model_name))
        else:
            cursor.execute("""
                SELECT forecast_date, model_name, model_version, horizon_hours, predicted_close, confidence_lower, confidence_upper
                FROM forecasts
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (symbol,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'forecast_date': row[0],
            'model_name': row[1],
            'model_version': row[2],
            'horizon_hours': row[3],
            'predicted_close': row[4],
            'confidence_lower': row[5],
            'confidence_upper': row[6]
        }

    # ---------------- Portfolio helpers -----------------

    def ensure_portfolio(self, name: str, strategy: str, initial_cash: float) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, cash, initial_cash, strategy, created_at, updated_at
            FROM portfolios
            WHERE name = ?
        """, (name,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {
                'id': row[0],
                'name': row[1],
                'cash': row[2],
                'initial_cash': row[3],
                'strategy': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }
        cursor.execute("""
            INSERT INTO portfolios (name, description, strategy, cash, initial_cash)
            VALUES (?, ?, ?, ?, ?)
        """, (name, f"{name} auto-managed portfolio", strategy, initial_cash, initial_cash))
        conn.commit()
        portfolio_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, name, cash, initial_cash, strategy, created_at, updated_at
            FROM portfolios WHERE id = ?
        """, (portfolio_id,))
        row = cursor.fetchone()
        conn.close()
        return {
            'id': row[0],
            'name': row[1],
            'cash': row[2],
            'initial_cash': row[3],
            'strategy': row[4],
            'created_at': row[5],
            'updated_at': row[6]
        }

    def update_portfolio_cash(self, portfolio_id: int, cash: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE portfolios
            SET cash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (cash, portfolio_id))
        conn.commit()
        conn.close()

    def get_portfolio_positions(self, portfolio_id: int) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, quantity, avg_price, updated_at
            FROM portfolio_positions
            WHERE portfolio_id = ?
        """, (portfolio_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {'symbol': row[0], 'quantity': row[1], 'avg_price': row[2], 'updated_at': row[3]}
            for row in rows
        ]

    def upsert_position(self, portfolio_id: int, symbol: str, quantity: float, avg_price: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        if quantity <= 0:
            cursor.execute("""
                DELETE FROM portfolio_positions
                WHERE portfolio_id = ? AND symbol = ?
            """, (portfolio_id, symbol))
        else:
            cursor.execute("""
                INSERT INTO portfolio_positions (portfolio_id, symbol, quantity, avg_price)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(portfolio_id, symbol) DO UPDATE SET
                    quantity = excluded.quantity,
                    avg_price = excluded.avg_price,
                    updated_at = CURRENT_TIMESTAMP
            """, (portfolio_id, symbol, quantity, avg_price))
        conn.commit()
        conn.close()

    def record_trade(self, portfolio_id: int, symbol: str, action: str,
                     quantity: float, price: float, reason: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio_trades (portfolio_id, symbol, action, quantity, price, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (portfolio_id, symbol, action, quantity, price, reason))
        conn.commit()
        conn.close()

    def record_equity_snapshot(self, portfolio_id: int, equity: float,
                               cash: float, holdings_value: float,
                               returns: float, volatility: float, sharpe: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio_equity
            (portfolio_id, equity, cash, holdings_value, returns, volatility, sharpe)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (portfolio_id, equity, cash, holdings_value, returns, volatility, sharpe))
        conn.commit()
        conn.close()

    def get_portfolio_equity_history(self, portfolio_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT snapshot_time, equity, cash, holdings_value, returns, volatility, sharpe
            FROM portfolio_equity
            WHERE portfolio_id = ?
            ORDER BY snapshot_time DESC
            LIMIT ?
        """, (portfolio_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'snapshot_time': row[0],
                'equity': row[1],
                'cash': row[2],
                'holdings_value': row[3],
                'returns': row[4],
                'volatility': row[5],
                'sharpe': row[6]
            }
            for row in rows
        ]

    def get_recent_trades(self, portfolio_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, action, quantity, price, reason, created_at
            FROM portfolio_trades
            WHERE portfolio_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (portfolio_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'symbol': row[0],
                'action': row[1],
                'quantity': row[2],
                'price': row[3],
                'reason': row[4],
                'created_at': row[5]
            }
            for row in rows
        ]

