import os
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database
from services.evaluation_service import EvaluationService
from services.portfolio_service import PortfolioService


class ServiceSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, 'services.db')
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _seed_data(self):
        self.db.insert_historical_data('AAPL', [
            {'date': '2024-01-01', 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000,
             'return_1d': 0.0, 'vol_5d': 0.0, 'sma_5': 100, 'sma_20': 100},
            {'date': '2024-01-02', 'open': 101, 'high': 102, 'low': 100, 'close': 101.5, 'volume': 1100,
             'return_1d': 0.01, 'vol_5d': 0.01, 'sma_5': 100.3, 'sma_20': 100.1},
        ])

    def test_evaluation_service_runs(self):
        self._seed_data()
        self.db.insert_forecast(
            symbol='AAPL',
            model_name='arima',
            forecast_date='2024-01-01',
            horizon_hours=24,
            predictions={'predicted_close': 102.0}
        )
        conn = self.db.get_connection()
        conn.execute("UPDATE forecasts SET created_at = datetime('now', '-2 hours')")
        conn.commit()
        conn.close()

        service = EvaluationService(self.db)
        result = service.evaluate_pending()
        self.assertIn('completed', result)

    def test_portfolio_service_summary(self):
        self._seed_data()
        service = PortfolioService(self.db)
        summary = service.summary()
        self.assertIn('portfolio', summary)
        self.assertIn('equity', summary)


if __name__ == '__main__':
    unittest.main()
