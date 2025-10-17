"""
MongoDB backend implementing the same interface as SQLite Database.
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING


class MongoDatabase:
    def __init__(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        db_name = os.environ.get('MONGO_DB', 'fintech_forecasting')
        self.db = self.client[db_name]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self.db.historical_prices.create_index([('symbol', ASCENDING), ('date', ASCENDING)], unique=True)
        self.db.sentiment_data.create_index([('symbol', ASCENDING), ('date', ASCENDING)], unique=True)
        self.db.forecasts.create_index([('symbol', ASCENDING), ('model_name', ASCENDING), ('forecast_date', ASCENDING), ('horizon_hours', ASCENDING)], unique=True)
        self.db.model_metrics.create_index([('symbol', ASCENDING), ('model_name', ASCENDING)])

    def insert_historical_data(self, symbol: str, data: List[Dict[str, Any]]):
        for row in data:
            doc = {**row, 'symbol': symbol}
            self.db.historical_prices.update_one(
                {'symbol': symbol, 'date': row['date']},
                {'$set': doc},
                upsert=True
            )

    def insert_sentiment_data(self, symbol: str, data: List[Dict[str, Any]]):
        for row in data:
            doc = {**row, 'symbol': symbol}
            self.db.sentiment_data.update_one(
                {'symbol': symbol, 'date': row['date']},
                {'$set': doc},
                upsert=True
            )

    def get_historical_data(self, symbol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cursor = self.db.historical_prices.find({'symbol': symbol}, {'_id': 0}).sort('date', ASCENDING)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def insert_forecast(self, symbol: str, model_name: str, forecast_date: str, 
                        horizon_hours: int, predictions: Dict[str, float]):
        doc = {
            'symbol': symbol,
            'model_name': model_name,
            'forecast_date': forecast_date,
            'horizon_hours': horizon_hours,
            'predicted_open': predictions.get('predicted_open') or predictions.get('open'),
            'predicted_high': predictions.get('predicted_high') or predictions.get('high'),
            'predicted_low': predictions.get('predicted_low') or predictions.get('low'),
            'predicted_close': predictions.get('predicted_close') or predictions.get('close'),
            'confidence_lower': predictions.get('confidence_lower'),
            'confidence_upper': predictions.get('confidence_upper'),
            'created_at': datetime.utcnow().isoformat()
        }
        self.db.forecasts.update_one(
            {
                'symbol': symbol,
                'model_name': model_name,
                'forecast_date': forecast_date,
                'horizon_hours': horizon_hours
            },
            {'$set': doc},
            upsert=True
        )

    def get_forecasts(self, symbol: str, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        filt = {'symbol': symbol}
        if model_name:
            filt['model_name'] = model_name
        cursor = self.db.forecasts.find(filt, {'_id': 0}).sort('forecast_date', ASCENDING)
        return list(cursor)

    def save_model_metrics(self, symbol: str, model_name: str, metrics: Dict[str, Any]):
        doc = {
            'symbol': symbol,
            'model_name': model_name,
            'rmse': metrics.get('rmse'),
            'mae': metrics.get('mae'),
            'mape': metrics.get('mape'),
            'train_samples': metrics.get('train_samples'),
            'test_samples': metrics.get('test_samples'),
            'parameters': metrics.get('parameters', {}),
            'updated_at': datetime.utcnow().isoformat()
        }
        self.db.model_metrics.update_one(
            {'symbol': symbol, 'model_name': model_name},
            {'$set': doc},
            upsert=True
        )

    def get_model_metrics(self, symbol: str) -> List[Dict[str, Any]]:
        cursor = self.db.model_metrics.find({'symbol': symbol}, {'_id': 0}).sort('updated_at', -1)
        return list(cursor)

    def get_available_symbols(self) -> List[str]:
        return sorted({d['symbol'] for d in self.db.historical_prices.find({}, {'symbol': 1})})


