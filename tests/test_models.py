"""
Unit tests for forecasting models.
"""

import unittest
import numpy as np
import sys
import os
import tempfile

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.traditional_models import MovingAverageModel, ARIMAModel, ExponentialSmoothingModel
from database.models import Database
from services.evaluation_service import EvaluationService
from services.portfolio_service import PortfolioService


class TestMovingAverageModel(unittest.TestCase):
    """Test cases for Moving Average model."""
    
    def setUp(self):
        """Set up test data."""
        self.data = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        self.model = MovingAverageModel(window=5)
    
    def test_initialization(self):
        """Test model initialization."""
        self.assertEqual(self.model.window, 5)
        self.assertEqual(self.model.name, "MA_5")
    
    def test_fit(self):
        """Test model fitting."""
        self.model.fit(self.data)
        self.assertEqual(len(self.model.history), len(self.data))
    
    def test_predict(self):
        """Test prediction generation."""
        self.model.fit(self.data)
        predictions, confidence = self.model.predict(steps=3)
        
        self.assertEqual(len(predictions), 3)
        self.assertIsInstance(confidence, float)
        self.assertTrue(all(pred > 0 for pred in predictions))
    
    def test_evaluate(self):
        """Test model evaluation."""
        train = self.data[:7]
        test = self.data[7:]
        
        metrics = self.model.evaluate(train, test)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)
        self.assertTrue(metrics['rmse'] > 0)
        self.assertTrue(metrics['mae'] > 0)


class TestARIMAModel(unittest.TestCase):
    """Test cases for ARIMA model."""
    
    def setUp(self):
        """Set up test data."""
        # Generate synthetic trend data
        np.random.seed(42)
        trend = np.linspace(100, 120, 50)
        noise = np.random.normal(0, 2, 50)
        self.data = trend + noise
        self.model = ARIMAModel(order=(2, 1, 0))
    
    def test_initialization(self):
        """Test model initialization."""
        self.assertEqual(self.model.order, (2, 1, 0))
        self.assertEqual(self.model.name, "ARIMA_2_1_0")
    
    def test_fit(self):
        """Test model fitting."""
        self.model.fit(self.data)
        self.assertIsNotNone(self.model.fitted_model)
    
    def test_predict(self):
        """Test prediction generation."""
        self.model.fit(self.data)
        predictions, confidence = self.model.predict(steps=5)
        
        self.assertEqual(len(predictions), 5)
        self.assertIsInstance(confidence, float)
        self.assertTrue(all(pred > 0 for pred in predictions))
    
    def test_evaluate(self):
        """Test model evaluation."""
        train = self.data[:40]
        test = self.data[40:45]
        
        metrics = self.model.evaluate(train, test)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)


class TestExponentialSmoothingModel(unittest.TestCase):
    """Test cases for Exponential Smoothing model."""
    
    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        self.data = np.cumsum(np.random.randn(50)) + 100
        self.model = ExponentialSmoothingModel(trend='add')
    
    def test_initialization(self):
        """Test model initialization."""
        self.assertEqual(self.model.trend, 'add')
        self.assertEqual(self.model.name, "ExpSmooth_add")
    
    def test_fit(self):
        """Test model fitting."""
        self.model.fit(self.data)
        self.assertIsNotNone(self.model.fitted_model)
    
    def test_predict(self):
        """Test prediction generation."""
        self.model.fit(self.data)
        predictions, confidence = self.model.predict(steps=5)
        
        self.assertEqual(len(predictions), 5)
        self.assertIsInstance(confidence, float)
    
    def test_evaluate(self):
        """Test model evaluation."""
        train = self.data[:40]
        test = self.data[40:45]
        
        metrics = self.model.evaluate(train, test)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)


class TestModelComparison(unittest.TestCase):
    """Compare different models on same data."""
    
    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        trend = np.linspace(100, 120, 50)
        noise = np.random.normal(0, 1, 50)
        self.data = trend + noise
        self.train = self.data[:40]
        self.test = self.data[40:45]
    
    def test_all_models_run(self):
        """Test that all traditional models can run on same data."""
        models = [
            MovingAverageModel(window=5),
            ARIMAModel(order=(2, 1, 0)),
            ExponentialSmoothingModel(trend='add')
        ]
        
        results = []
        for model in models:
            try:
                metrics = model.evaluate(self.train, self.test)
                results.append({
                    'name': model.name,
                    'rmse': metrics['rmse'],
                    'mae': metrics['mae']
                })
            except Exception as e:
                self.fail(f"Model {model.name} failed: {e}")
        
        # Check that we got results from all models
        self.assertEqual(len(results), len(models))
        
        # Print comparison
        print("\n" + "=" * 60)
        print("Model Comparison Results:")
        print("=" * 60)
        for result in sorted(results, key=lambda x: x['rmse']):
            print(f"{result['name']:20s} - RMSE: {result['rmse']:.4f}, MAE: {result['mae']:.4f}")
        print("=" * 60)


class BaseServiceTestCase(unittest.TestCase):
    """Utility base class for database-backed service tests."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tempdir.name, "test.db")
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()


class TestModelRegistryIntegration(BaseServiceTestCase):
    def test_model_version_activation(self):
        self.db.insert_model_version(
            symbol="AAPL",
            model_name="arima",
            version="v1",
            status="ready",
            train_start="2024-01-01",
            train_end="2024-01-31",
            metrics={"rmse": 1.0},
            hyperparams={"window": 5},
            artifact_path="models_store/AAPL/arima/v1.pkl",
            activate=False,
        )
        self.db.insert_model_version(
            symbol="AAPL",
            model_name="arima",
            version="v2",
            status="ready",
            train_start="2024-02-01",
            train_end="2024-02-29",
            metrics={"rmse": 0.8},
            hyperparams={"window": 5},
            artifact_path="models_store/AAPL/arima/v2.pkl",
            activate=True,
        )

        active = self.db.get_active_model_version("AAPL", "arima")
        self.assertIsNotNone(active)
        self.assertEqual(active["version"], "v2")


class TestEvaluationPipeline(BaseServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = EvaluationService(self.db)
        self.db.insert_historical_data("AAPL", [
            {"date": "2024-01-01", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000,
             "return_1d": 0.0, "vol_5d": 0.0, "sma_5": 100, "sma_20": 100},
            {"date": "2024-01-02", "open": 101, "high": 102, "low": 100, "close": 101.5, "volume": 1200,
             "return_1d": 0.01, "vol_5d": 0.02, "sma_5": 100.4, "sma_20": 100.1},
        ])

    def test_evaluate_pending(self):
        self.db.insert_forecast(
            symbol="AAPL",
            model_name="arima",
            forecast_date="2024-01-01",
            horizon_hours=24,
            predictions={"predicted_close": 102.0},
        )

        conn = self.db.get_connection()
        conn.execute("UPDATE forecasts SET created_at = datetime('now', '-90 minutes')")
        conn.commit()
        conn.close()

        result = self.service.evaluate_pending()
        self.assertGreaterEqual(result["completed"], 1)

        errors = self.db.get_forecast_errors("AAPL", model_name="arima", limit=1)
        self.assertTrue(errors)
        self.assertIsNotNone(errors[0]["actual_close"])


class TestPortfolioServiceIntegration(BaseServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = PortfolioService(self.db)
        self.db.insert_historical_data("AAPL", [
            {"date": "2024-01-01", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000,
             "return_1d": 0.0, "vol_5d": 0.0, "sma_5": 100, "sma_20": 100},
        ])

    def test_summary_contains_expected_fields(self):
        summary = self.service.summary()
        self.assertIn("portfolio", summary)
        self.assertIn("equity", summary)
        self.assertIn("positions", summary)


if __name__ == '__main__':
    unittest.main(verbosity=2)

