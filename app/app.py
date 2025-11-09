"""
Flask backend for FinTech forecasting application.
Provides REST API for forecasting financial instruments.
"""

from flask import Flask, render_template, request, jsonify
from flask import send_from_directory
import sys
import os
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database as SqliteDatabase
from typing import Optional

MONGO_URI = os.environ.get('MONGO_URI')
USE_MONGO = os.environ.get('USE_MONGO', '0') == '1'

db: Optional[object] = None
try:
    if USE_MONGO and MONGO_URI:
        from database.mongo_db import MongoDatabase
        db = MongoDatabase(MONGO_URI)
    else:
        db = SqliteDatabase()
except Exception as e:
    # Fallback to SQLite on any error
    db = SqliteDatabase()
from models import get_traditional_factories, get_neural_factories, KERAS_AVAILABLE
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from services.adaptive_service import AdaptiveLearningService
from services.evaluation_service import EvaluationService
from services.ingestion_service import IngestionService
from services.portfolio_service import PortfolioService

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# db is initialized above via env-based selector

TRADITIONAL_MODELS = get_traditional_factories()
NEURAL_MODELS = get_neural_factories()

adaptive_service = AdaptiveLearningService(db)
evaluation_service = EvaluationService(db)
ingestion_service = IngestionService(db)
portfolio_service = PortfolioService(db)


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """Serve favicon for browsers expecting /favicon.ico."""
    try:
        return send_from_directory(app.static_folder, 'favicon.svg')
    except Exception:
        return '', 204


@app.route('/health')
def health():
    try:
        symbols = db.get_available_symbols()
        return jsonify({'status': 'healthy', 'symbols': symbols}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/ingest', methods=['POST'])
def trigger_ingestion():
    """Manually trigger data ingestion."""
    payload = request.json or {}
    symbol = payload.get('symbol')
    try:
        if symbol:
            result = ingestion_service.ingest(symbol)
        else:
            result = ingestion_service.ingest_all()
        return jsonify({'status': 'ok', 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/train', methods=['POST'])
def trigger_training():
    """Train or update a model version."""
    data = request.json or {}
    symbol = data.get('symbol')
    model_name = data.get('model', 'arima')
    mode = data.get('mode', 'full')
    lookback = data.get('lookback')
    activate = data.get('activate', True)

    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
    try:
        lookback_int = int(lookback) if lookback else None
        result = adaptive_service.train(
            symbol=symbol,
            model_name=model_name,
            mode=mode,
            lookback=lookback_int,
            activate=activate
        )
        return jsonify({'status': 'ok', 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models/versions')
def list_model_versions():
    """Return model version history for a symbol."""
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'symbol query parameter required'}), 400
    model_name = request.args.get('model')
    versions = db.get_model_versions(symbol, model_name=model_name)
    return jsonify({'symbol': symbol, 'versions': versions})


@app.route('/api/models/activate', methods=['POST'])
def activate_model_version():
    data = request.json or {}
    symbol = data.get('symbol')
    model_name = data.get('model')
    version = data.get('version')
    if not all([symbol, model_name, version]):
        return jsonify({'error': 'symbol, model, and version required'}), 400
    try:
        db.set_active_model_version(symbol, model_name, version)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/symbols')
def get_symbols():
    """Get available symbols."""
    try:
        symbols = db.get_available_symbols()
        return jsonify({'symbols': symbols})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/historical/<symbol>')
def get_historical(symbol):
    """Get historical data for a symbol."""
    try:
        data = db.get_historical_data(symbol)
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/errors/<symbol>')
def get_error_series(symbol):
    """Return evaluated forecast errors for monitoring overlays."""
    model_name = request.args.get('model')
    try:
        limit = int(request.args.get('limit', 100))
    except ValueError:
        limit = 100
    try:
        series = evaluation_service.error_series(symbol, model_name=model_name, limit=limit)
        return jsonify({'symbol': symbol, 'errors': series})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics/rolling/<symbol>')
def get_rolling_metrics(symbol):
    """Return rolling metrics summary for dashboards."""
    try:
        window = request.args.get('window')
        window_int = int(window) if window else None
    except ValueError:
        window_int = None
    try:
        metrics = evaluation_service.rolling_metrics(symbol, window=window_int)
        return jsonify({'symbol': symbol, 'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/forecast', methods=['POST'])
def generate_forecast():
    """
    Generate forecast for a symbol using specified model.
    
    Request JSON:
    {
        "symbol": "AAPL",
        "model": "lstm",
        "horizon_hours": 24
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        model_name = data.get('model', 'arima')
        horizon_hours = max(1, int(data.get('horizon_hours', 24)))
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        # Get historical data
        historical = db.get_historical_data(symbol)
        if not historical:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Extract close prices
        prices = np.array([d['close'] for d in historical], dtype=float)
        if len(prices) < 5:
            return jsonify({'error': 'Insufficient historical data for forecasting'}), 400
        
        # Calculate number of steps (assuming daily data, convert hours to days)
        steps = max(1, math.ceil(horizon_hours / 24))
        step_hours = round(horizon_hours / steps, 2)
        
        version_meta = None
        try:
            loaded_model, version_meta = adaptive_service.load_active_model(symbol, model_name)
        except Exception:
            loaded_model = None

        if loaded_model:
            model = loaded_model
            predictions, confidence = adaptive_service.predict_with_model(model, prices, steps)
        else:
            # Select model (with graceful fallback for neural models if data is short)
            if model_name in TRADITIONAL_MODELS:
                model = TRADITIONAL_MODELS[model_name]()
                model.fit(prices)
                predictions, confidence = model.predict(steps=steps)
            elif model_name in NEURAL_MODELS:
                candidate = NEURAL_MODELS[model_name]()
                required_len = getattr(candidate, 'lookback', 10) + 5
                if len(prices) < required_len:
                    model = TRADITIONAL_MODELS['arima']()
                    model.fit(prices)
                    predictions, confidence = model.predict(steps=steps)
                else:
                    model = candidate
                    model.fit(prices)
                    predictions, confidence = model.predict(prices, steps=steps)
            else:
                return jsonify({'error': f'Unknown model: {model_name}'}), 400

        model_version = version_meta.get('version') if version_meta else None
        model_source = 'registry' if version_meta else 'adhoc'
        model_display_name = getattr(model, 'name', model_name)
        
        # Generate forecast dates
        last_date_str = historical[-1]['date']
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        forecast_dates = []
        for i in range(steps):
            delta_hours = step_hours * (i + 1)
            forecast_dt = last_date + timedelta(hours=delta_hours)
            # Use ISO-like strings; include time component for sub-daily horizons
            if forecast_dt.hour == 0 and forecast_dt.minute == 0:
                forecast_dates.append(forecast_dt.strftime('%Y-%m-%d'))
            else:
                forecast_dates.append(forecast_dt.strftime('%Y-%m-%d %H:%M'))
        
        # Prepare forecast response
        forecasts = []
        try:
            confidence_band = float(confidence)
        except (TypeError, ValueError):
            confidence_band = 0.0
        volatility_base = confidence_band * 0.5

        for i, (date, pred) in enumerate(zip(forecast_dates, predictions)):
            # Estimate OHLC based on prediction and volatility
            volatility = volatility_base
            forecast_item = {
                'date': date,
                'horizon_hours': horizon_hours,
                'step_hours': step_hours,
                'model_version': model_version,
                'predicted_open': float(pred - volatility * 0.3),
                'predicted_high': float(pred + volatility),
                'predicted_low': float(pred - volatility),
                'predicted_close': float(pred),
                'confidence_lower': float(pred - confidence_band),
                'confidence_upper': float(pred + confidence_band)
            }
            forecasts.append(forecast_item)
            
            # Save to database
            db.insert_forecast(
                symbol=symbol,
                model_name=model.name,
                forecast_date=date,
                horizon_hours=horizon_hours,
                predictions=forecast_item
            )
        
        return jsonify({
            'symbol': symbol,
            'model': model_display_name,
            'model_version': model_version,
            'model_source': model_source,
            'horizon_hours': horizon_hours,
            'forecasts': forecasts
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/forecasts/<symbol>')
def get_saved_forecasts(symbol: str):
    """Return previously saved forecasts for a symbol (all models)."""
    try:
        rows = db.get_forecasts(symbol)
        return jsonify({'forecasts': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate_models():
    """
    Evaluate multiple models on a symbol.
    
    Request JSON:
    {
        "symbol": "AAPL",
        "test_size": 5
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        test_size = int(data.get('test_size', 5))
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        # Get historical data
        historical = db.get_historical_data(symbol)
        if not historical:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        prices = np.array([d['close'] for d in historical])
        
        if len(prices) < test_size + 10:
            # Adapt test window for shorter histories
            adaptive_size = max(2, len(prices) // 3)
            if adaptive_size < test_size:
                test_size = adaptive_size
        
        if len(prices) < test_size + 5 or test_size < 2:
            return jsonify({'error': 'Insufficient data for evaluation'}), 400
        
        # Split data
        train = prices[:-test_size]
        test = prices[-test_size:]
        
        # Evaluate all models
        results = []
        
        # Traditional models
        for model_key, model_fn in TRADITIONAL_MODELS.items():
            try:
                model = model_fn()
                metrics = model.evaluate(train, test)
                metrics['model_name'] = getattr(model, 'name', model_key)
                metrics['model_type'] = 'traditional'
                results.append(metrics)
                
                # Save metrics to database
                db.save_model_metrics(symbol, model.name, metrics)
            except Exception as e:
                print(f"Error evaluating {model_key}: {e}")
        
        # Neural models
        for model_key, model_fn in NEURAL_MODELS.items():
            try:
                model = model_fn()
                metrics = model.evaluate(train, test)
                metrics['model_name'] = getattr(model, 'name', model_key)
                metrics['model_type'] = 'neural'
                results.append(metrics)
                
                # Save metrics to database
                db.save_model_metrics(symbol, model.name, metrics)
            except Exception as e:
                print(f"Error evaluating {model_key}: {e}")
        
        if not results:
            return jsonify({'error': 'No models produced evaluation metrics'}), 500
        
        # Determine best model (prioritize RMSE, then MAE, then MAPE)
        best_model = min(
            results,
            key=lambda m: (m.get('rmse', float('inf')),
                           m.get('mae', float('inf')),
                           m.get('mape', float('inf')))
        )
        
        return jsonify({
            'symbol': symbol,
            'test_size': test_size,
            'results': results,
            'best_model': best_model
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics/<symbol>')
def get_metrics(symbol):
    """Get model performance metrics for a symbol."""
    try:
        metrics = db.get_model_metrics(symbol)
        return jsonify({'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models')
def get_available_models():
    """Get list of available models."""
    models = {
        'traditional': list(TRADITIONAL_MODELS.keys()),
        'neural': list(NEURAL_MODELS.keys()) if KERAS_AVAILABLE else [],
        'all': adaptive_service.get_available_models()
    }
    return jsonify(models)


@app.route('/api/portfolio/summary')
def portfolio_summary():
    try:
        data = portfolio_service.summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/run', methods=['POST'])
def portfolio_run():
    try:
        data = portfolio_service.run_auto_strategy()
        return jsonify({'status': 'ok', 'result': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/trade', methods=['POST'])
def portfolio_trade():
    payload = request.json or {}
    symbol = payload.get('symbol')
    action = payload.get('action')
    quantity = payload.get('quantity')
    price = payload.get('price')
    if not symbol or not action or not quantity:
        return jsonify({'error': 'symbol, action, and quantity required'}), 400
    try:
        quantity = float(quantity)
    except ValueError:
        return jsonify({'error': 'quantity must be numeric'}), 400
    try:
        price_val = float(price) if price is not None else None
        data = portfolio_service.manual_trade(symbol, action, quantity, price_val)
        return jsonify({'status': 'ok', 'result': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
