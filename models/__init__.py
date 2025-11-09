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

def get_traditional_factories():
    """Return factory map for traditional models."""
    return {
        'ma_5': lambda: MovingAverageModel(window=5),
        'ma_10': lambda: MovingAverageModel(window=10),
        'arima': lambda: ARIMAModel(order=(5, 1, 0)),
        'exp_smooth': lambda: ExponentialSmoothingModel(trend='add'),
    }


def get_neural_factories():
    """Return factory map for neural models (only when TensorFlow available)."""
    if not KERAS_AVAILABLE:
        return {}
    return {
        'lstm': lambda: LSTMModel(lookback=10, units=50),
        'gru': lambda: GRUModel(lookback=10, units=50),
    }


__all__ = [
    'MovingAverageModel',
    'ARIMAModel',
    'ExponentialSmoothingModel',
    'LSTMModel',
    'GRUModel',
    'KERAS_AVAILABLE',
    'get_traditional_factories',
    'get_neural_factories',
]

