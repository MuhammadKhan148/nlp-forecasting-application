"""
Neural network forecasting models: LSTM, GRU
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
import os
warnings.filterwarnings('ignore')

# Try to import TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("Warning: TensorFlow not available. Neural models will not work.")

DEFAULT_EPOCHS = max(10, int(os.environ.get('NEURAL_EPOCHS', '30')))
DEFAULT_PATIENCE = max(3, int(os.environ.get('NEURAL_PATIENCE', '5')))


def create_sequences(data: np.ndarray, lookback: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sequences for time series prediction.
    
    Args:
        data: Input time series data
        lookback: Number of timesteps to look back
        
    Returns:
        Tuple of (X, y) where X is input sequences and y is targets
    """
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i+lookback])
        y.append(data[i+lookback])
    return np.array(X), np.array(y)


class LSTMModel:
    """LSTM (Long Short-Term Memory) neural network for time series forecasting."""
    
    def __init__(self, lookback: int = 10, units: int = 50, dropout: float = 0.2):
        """
        Initialize LSTM model.
        
        Args:
            lookback: Number of previous timesteps to use
            units: Number of LSTM units
            dropout: Dropout rate for regularization
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras required for LSTM model")
        
        self.lookback = lookback
        self.units = units
        self.dropout = dropout
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        self.name = f"LSTM_{units}"
        self.max_epochs = DEFAULT_EPOCHS
        self.patience = DEFAULT_PATIENCE
        self.last_history = None
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using z-score normalization."""
        self.scaler_mean = np.mean(data)
        self.scaler_std = np.std(data)
        return (data - self.scaler_mean) / (self.scaler_std + 1e-8)
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data."""
        return data * self.scaler_std + self.scaler_mean
    
    def build_model(self):
        """Build LSTM architecture."""
        model = Sequential([
            LSTM(self.units, return_sequences=True, input_shape=(self.lookback, 1)),
            Dropout(self.dropout),
            LSTM(self.units // 2, return_sequences=False),
            Dropout(self.dropout),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def fit(self, data: np.ndarray, epochs: Optional[int] = None, batch_size: int = 32, verbose: int = 0):
        """
        Train LSTM model.
        
        Args:
            data: Historical price data
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level
        """
        data = np.asarray(data, dtype=float)
        
        if len(data) < self.lookback:
            raise ValueError(f"Need at least {self.lookback} observations for prediction")
        
        # Normalize data using training statistics when available
        if self.scaler_mean is None or self.scaler_std is None:
            normalized_data = self._normalize(data)
        else:
            normalized_data = (data - self.scaler_mean) / (self.scaler_std + 1e-8)
        
        # Create sequences
        X, y = create_sequences(normalized_data, self.lookback)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Build model
        self.model = self.build_model()
        
        # Early stopping
        epochs = epochs if epochs is not None else self.max_epochs
        patience = min(self.patience, max(1, epochs // 4))
        early_stop = EarlyStopping(monitor='loss', patience=patience, restore_best_weights=True)
        
        # Train model
        self.last_history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=[early_stop],
            validation_split=0.1
        )
    
    def predict(self, data: np.ndarray, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecasts.
        
        Args:
            data: Recent historical data (at least lookback points)
            steps: Number of steps ahead to forecast
            
        Returns:
            Tuple of (predictions, confidence interval width)
        """
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")
        
        data = np.asarray(data, dtype=float)
        
        if len(data) < self.lookback:
            raise ValueError(f"Need at least {self.lookback} observations for prediction")
        
        if self.scaler_mean is None or self.scaler_std is None:
            normalized_data = self._normalize(data)
        else:
            normalized_data = (data - self.scaler_mean) / (self.scaler_std + 1e-8)
        
        predictions = []
        current_sequence = normalized_data[-self.lookback:].copy()
        
        for _ in range(steps):
            # Reshape for prediction
            X = current_sequence.reshape(1, self.lookback, 1)
            
            # Predict next value
            pred_normalized = self.model.predict(X, verbose=0)[0, 0]
            predictions.append(pred_normalized)
            
            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred_normalized)
        
        # Denormalize predictions
        predictions = self._denormalize(np.array(predictions))
        
        # Estimate confidence interval from training volatility
        train_volatility = self.scaler_std
        confidence = train_volatility * 1.96  # 95% confidence
        
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
        self.fit(train, epochs=self.max_epochs, verbose=0)
        
        # Use last lookback points from train for context
        context = train[-self.lookback:]
        predictions, _ = self.predict(context, steps=len(test))
        
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'train_samples': len(train),
            'test_samples': len(test),
            'parameters': {
                'lookback': self.lookback,
                'units': self.units,
                'dropout': self.dropout
            }
        }


class GRUModel:
    """GRU (Gated Recurrent Unit) neural network for time series forecasting."""
    
    def __init__(self, lookback: int = 10, units: int = 50, dropout: float = 0.2):
        """
        Initialize GRU model.
        
        Args:
            lookback: Number of previous timesteps to use
            units: Number of GRU units
            dropout: Dropout rate for regularization
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras required for GRU model")
        
        self.lookback = lookback
        self.units = units
        self.dropout = dropout
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        self.name = f"GRU_{units}"
        self.max_epochs = DEFAULT_EPOCHS
        self.patience = DEFAULT_PATIENCE
        self.last_history = None
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using z-score normalization."""
        self.scaler_mean = np.mean(data)
        self.scaler_std = np.std(data)
        return (data - self.scaler_mean) / (self.scaler_std + 1e-8)
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data."""
        return data * self.scaler_std + self.scaler_mean
    
    def build_model(self):
        """Build GRU architecture."""
        model = Sequential([
            GRU(self.units, return_sequences=True, input_shape=(self.lookback, 1)),
            Dropout(self.dropout),
            GRU(self.units // 2, return_sequences=False),
            Dropout(self.dropout),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def fit(self, data: np.ndarray, epochs: Optional[int] = None, batch_size: int = 32, verbose: int = 0):
        """
        Train GRU model.
        
        Args:
            data: Historical price data
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level
        """
        # Normalize data
        normalized_data = self._normalize(data)
        
        # Create sequences
        X, y = create_sequences(normalized_data, self.lookback)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Build model
        self.model = self.build_model()
        
        # Early stopping
        epochs = epochs if epochs is not None else self.max_epochs
        patience = min(self.patience, max(1, epochs // 4))
        early_stop = EarlyStopping(monitor='loss', patience=patience, restore_best_weights=True)
        
        # Train model
        self.last_history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=[early_stop],
            validation_split=0.1
        )
    
    def predict(self, data: np.ndarray, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecasts.
        
        Args:
            data: Recent historical data (at least lookback points)
            steps: Number of steps ahead to forecast
            
        Returns:
            Tuple of (predictions, confidence interval width)
        """
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")
        
        # Normalize data
        normalized_data = self._normalize(data)
        
        predictions = []
        current_sequence = normalized_data[-self.lookback:].copy()
        
        for _ in range(steps):
            # Reshape for prediction
            X = current_sequence.reshape(1, self.lookback, 1)
            
            # Predict next value
            pred_normalized = self.model.predict(X, verbose=0)[0, 0]
            predictions.append(pred_normalized)
            
            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred_normalized)
        
        # Denormalize predictions
        predictions = self._denormalize(np.array(predictions))
        
        # Estimate confidence interval from training volatility
        train_volatility = self.scaler_std
        confidence = train_volatility * 1.96  # 95% confidence
        
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
        self.fit(train, epochs=self.max_epochs, verbose=0)
        
        # Use last lookback points from train for context
        context = train[-self.lookback:]
        predictions, _ = self.predict(context, steps=len(test))
        
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'train_samples': len(train),
            'test_samples': len(test),
            'parameters': {
                'lookback': self.lookback,
                'units': self.units,
                'dropout': self.dropout
            }
        }

