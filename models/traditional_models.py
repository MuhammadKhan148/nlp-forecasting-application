"""
Traditional forecasting models: ARIMA, Moving Average, Exponential Smoothing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')


class MovingAverageModel:
    """Simple Moving Average forecasting model."""
    
    def __init__(self, window: int = 5):
        """
        Initialize Moving Average model.
        
        Args:
            window: Number of periods for moving average
        """
        self.window = window
        self.history = []
        self.name = f"MA_{window}"
    
    def fit(self, data: np.ndarray):
        """
        Fit the model with historical data.
        
        Args:
            data: Array of historical prices
        """
        self.history = list(data)
    
    def predict(self, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecasts.
        
        Args:
            steps: Number of steps ahead to forecast
            
        Returns:
            Tuple of (predictions, confidence intervals)
        """
        predictions = []
        temp_history = self.history.copy()
        
        for _ in range(steps):
            # Use last 'window' values for prediction
            recent = temp_history[-self.window:]
            pred = np.mean(recent)
            predictions.append(pred)
            temp_history.append(pred)
        
        predictions = np.array(predictions)
        
        # Calculate simple confidence intervals based on historical volatility
        volatility = np.std(self.history[-self.window:])
        confidence = volatility * 1.96  # 95% confidence
        
        return predictions, confidence
    
    def evaluate(self, train: np.ndarray, test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            train: Training data
            test: Test data
            
        Returns:
            Dictionary of metrics (RMSE, MAE, MAPE)
        """
        self.fit(train)
        predictions, _ = self.predict(steps=len(test))
        
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'train_samples': len(train),
            'test_samples': len(test),
            'parameters': {'window': self.window}
        }


class ARIMAModel:
    """ARIMA (AutoRegressive Integrated Moving Average) forecasting model."""
    
    def __init__(self, order: Tuple[int, int, int] = (5, 1, 0)):
        """
        Initialize ARIMA model.
        
        Args:
            order: (p, d, q) order for ARIMA
                   p: AR order, d: differencing order, q: MA order
        """
        self.order = order
        self.model = None
        self.fitted_model = None
        self.name = f"ARIMA_{order[0]}_{order[1]}_{order[2]}"
    
    def fit(self, data: np.ndarray):
        """
        Fit ARIMA model to data.
        
        Args:
            data: Array of historical prices
        """
        try:
            self.model = ARIMA(data, order=self.order)
            self.fitted_model = self.model.fit()
        except Exception as e:
            print(f"ARIMA fit failed: {e}")
            # Fallback to simpler model
            self.order = (1, 1, 1)
            self.model = ARIMA(data, order=self.order)
            self.fitted_model = self.model.fit()
    
    def predict(self, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecasts with confidence intervals.
        
        Args:
            steps: Number of steps ahead to forecast
            
        Returns:
            Tuple of (predictions, confidence intervals)
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before prediction")
        
        forecast_result = self.fitted_model.forecast(steps=steps)
        
        # Get confidence intervals if available
        forecast_obj = self.fitted_model.get_forecast(steps=steps)
        conf_int = forecast_obj.conf_int()
        
        predictions = np.array(forecast_result)
        # Calculate width of confidence interval
        confidence = (conf_int.iloc[:, 1] - conf_int.iloc[:, 0]).mean() / 2
        
        return predictions, float(confidence)
    
    def evaluate(self, train: np.ndarray, test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            train: Training data
            test: Test data
            
        Returns:
            Dictionary of metrics (RMSE, MAE, MAPE)
        """
        self.fit(train)
        predictions, _ = self.predict(steps=len(test))
        
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'train_samples': len(train),
            'test_samples': len(test),
            'parameters': {'order': self.order}
        }


class ExponentialSmoothingModel:
    """Exponential Smoothing (Holt-Winters) forecasting model."""
    
    def __init__(self, seasonal_periods: int = 5, trend: str = 'add'):
        """
        Initialize Exponential Smoothing model.
        
        Args:
            seasonal_periods: Number of periods in a season
            trend: Type of trend component ('add', 'mul', or None)
        """
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.model = None
        self.fitted_model = None
        self.name = f"ExpSmooth_{trend}"
    
    def fit(self, data: np.ndarray):
        """
        Fit Exponential Smoothing model.
        
        Args:
            data: Array of historical prices
        """
        try:
            # Only use trend, no seasonality for short series
            self.model = ExponentialSmoothing(
                data,
                trend=self.trend,
                seasonal=None
            )
            self.fitted_model = self.model.fit()
        except Exception as e:
            print(f"ExponentialSmoothing fit failed: {e}")
            # Fallback to simple model
            self.trend = None
            self.model = ExponentialSmoothing(data, trend=None, seasonal=None)
            self.fitted_model = self.model.fit()
    
    def predict(self, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecasts.
        
        Args:
            steps: Number of steps ahead to forecast
            
        Returns:
            Tuple of (predictions, confidence intervals)
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before prediction")
        
        predictions = self.fitted_model.forecast(steps=steps)
        
        # Simple confidence interval based on residuals
        residuals = self.fitted_model.resid
        std_resid = np.std(residuals)
        confidence = std_resid * 1.96  # 95% confidence
        
        return np.array(predictions), float(confidence)
    
    def evaluate(self, train: np.ndarray, test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            train: Training data
            test: Test data
            
        Returns:
            Dictionary of metrics (RMSE, MAE, MAPE)
        """
        self.fit(train)
        predictions, _ = self.predict(steps=len(test))
        
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'train_samples': len(train),
            'test_samples': len(test),
            'parameters': {'trend': self.trend}
        }

