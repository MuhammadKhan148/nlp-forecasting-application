"""Continuous evaluation of forecasts."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List

from .config_service import CONFIG

LOGGER = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, db):
        self.db = db

    def _target_date(self, forecast: Dict) -> str:
        forecast_dt = datetime.fromisoformat(forecast["forecast_date"])
        horizon = timedelta(hours=int(forecast.get("horizon_hours", 1)))
        return (forecast_dt + horizon).date().isoformat()

    def evaluate_pending(self) -> Dict[str, int]:
        pending = self.db.get_pending_forecasts()
        completed = 0
        skipped = 0
        for forecast in pending:
            target_date = self._target_date(forecast)
            actual = self.db.get_price_for_date(forecast["symbol"], target_date)
            if not actual:
                skipped += 1
                continue
            actual_close = actual["close"]
            predicted_close = forecast.get("predicted_close") or forecast.get("close")
            if predicted_close is None:
                skipped += 1
                continue
            error_abs = abs(actual_close - predicted_close)
            error_pct = (error_abs / actual_close) * 100 if actual_close else 0
            self.db.update_forecast_evaluation(
                forecast_id=forecast["id"],
                actual_close=actual_close,
                error_abs=error_abs,
                error_pct=error_pct,
            )
            self.db.insert_metrics_history(
                symbol=forecast["symbol"],
                model_name=forecast["model_name"],
                horizon_hours=forecast["horizon_hours"],
                rmse=error_abs,  # single-point approximation; rolling handled later
                mae=error_abs,
                mape=error_pct,
            )
            completed += 1
        return {"completed": completed, "skipped": skipped}

    def rolling_metrics(self, symbol: str, window: int | None = None) -> Dict[str, float | int]:
        window = window or CONFIG.forecast_error_window
        rows = self.db.get_metrics_history(symbol, limit_days=window)
        if not rows:
            return {"count": 0, "rmse": None, "mae": None, "mape": None}
        rmse = (mean([row["rmse"] ** 2 for row in rows]) or 0) ** 0.5
        mae = mean(row["mae"] for row in rows)
        mape = mean(row["mape"] for row in rows)
        return {"count": len(rows), "rmse": rmse, "mae": mae, "mape": mape}

    def error_series(self, symbol: str, model_name: str | None = None, limit: int = 100) -> List[Dict]:
        return self.db.get_forecast_errors(symbol, model_name=model_name, limit=limit)
