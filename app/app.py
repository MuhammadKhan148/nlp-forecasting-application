"""
Flask backend for FinTech forecasting application.
Provides REST API for forecasting financial instruments.
"""

from flask import Flask, render_template, request, jsonify
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database
from models.traditional_models import MovingAverageModel, ARIMAModel, ExponentialSmoothingModel
from models.neural_models import LSTMModel, GRUModel, KERAS_AVAILABLE
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# Initialize database
db = Database()

# Available models
TRADITIONAL_MODELS = {
    'ma_5': lambda: MovingAverageModel(window=5),
    'ma_10': lambda: MovingAverageModel(window=10),
    'arima': lambda: ARIMAModel(order=(5, 1, 0)),
    'exp_smooth': lambda: ExponentialSmoothingModel(trend='add')
}

NEURAL_MODELS = {}
if KERAS_AVAILABLE:
    NEURAL_MODELS = {
        'lstm': lambda: LSTMModel(lookback=10, units=50),
        'gru': lambda: GRUModel(lookback=10, units=50)
    }


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


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
        horizon_hours = int(data.get('horizon_hours', 24))
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        # Get historical data
        historical = db.get_historical_data(symbol)
        if not historical:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Extract close prices
        prices = np.array([d['close'] for d in historical])
        
        # Calculate number of steps (assuming daily data, convert hours to days)
        steps = max(1, horizon_hours // 24)
        
        # Select and train model
        if model_name in TRADITIONAL_MODELS:
            model = TRADITIONAL_MODELS[model_name]()
        elif model_name in NEURAL_MODELS:
            model = NEURAL_MODELS[model_name]()
        else:
            return jsonify({'error': f'Unknown model: {model_name}'}), 400
        
        # Fit model
        model.fit(prices)
        
        # Generate predictions
        predictions, confidence = model.predict(steps=steps)
        
        # Generate forecast dates
        last_date = datetime.strptime(historical[-1]['date'], '%Y-%m-%d')
        forecast_dates = [
            (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
            for i in range(steps)
        ]
        
        # Prepare forecast response
        forecasts = []
        for i, (date, pred) in enumerate(zip(forecast_dates, predictions)):
            # Estimate OHLC based on prediction and volatility
            volatility = confidence * 0.5
            forecast_item = {
                'date': date,
                'predicted_open': float(pred - volatility * 0.3),
                'predicted_high': float(pred + volatility),
                'predicted_low': float(pred - volatility),
                'predicted_close': float(pred),
                'confidence_lower': float(pred - confidence),
                'confidence_upper': float(pred + confidence)
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
            'model': model.name,
            'horizon_hours': horizon_hours,
            'forecasts': forecasts
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
                metrics['model_type'] = 'neural'
                results.append(metrics)
                
                # Save metrics to database
                db.save_model_metrics(symbol, model.name, metrics)
            except Exception as e:
                print(f"Error evaluating {model_key}: {e}")
        
        return jsonify({
            'symbol': symbol,
            'test_size': test_size,
            'results': results
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
        'neural': list(NEURAL_MODELS.keys()) if KERAS_AVAILABLE else []
    }
    return jsonify(models)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

