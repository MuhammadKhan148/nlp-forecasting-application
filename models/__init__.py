"""
Forecasting models module.
Contains traditional and neural network models for time series prediction.
"""

from .traditional_models import MovingAverageModel, ARIMAModel, ExponentialSmoothingModel

try:
    from .neural_models import LSTMModel, GRUModel, KERAS_AVAILABLE
except ImportError:
    KERAS_AVAILABLE = False
    LSTMModel = None
    GRUModel = None

__all__ = [
    'MovingAverageModel',
    'ARIMAModel', 
    'ExponentialSmoothingModel',
    'LSTMModel',
    'GRUModel',
    'KERAS_AVAILABLE'
]

