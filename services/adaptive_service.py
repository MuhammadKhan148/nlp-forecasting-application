"""Adaptive and continuous learning helpers."""
from __future__ import annotations

import inspect
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from models import (
    KERAS_AVAILABLE,
    get_neural_factories,
    get_traditional_factories,
)

from .config_service import CONFIG

LOGGER = logging.getLogger(__name__)


class AdaptiveLearningService:
    def __init__(self, db):
        self.db = db
        self.model_store = Path(CONFIG.model_store_dir)
        self.model_store.mkdir(parents=True, exist_ok=True)
        self.factories: Dict[str, callable] = get_traditional_factories()
        self.factories.update(get_neural_factories())

    def _artifact_path(self, symbol: str, model_name: str, version: str) -> Path:
        return self.model_store / symbol / model_name / f"{version}.pkl"

    def train(
        self,
        symbol: str,
        model_name: str,
        mode: str = "full",
        lookback: Optional[int] = None,
        activate: bool = True,
    ) -> Dict:
        factory = self.factories.get(model_name)
        if factory is None:
            raise ValueError(f"Unsupported model: {model_name}")

        historical = self.db.get_historical_data(symbol)
        if not historical:
            raise ValueError(f"No data available for {symbol}")

        prices = np.array([row["close"] for row in historical], dtype=float)
        if lookback and len(prices) > lookback:
            prices = prices[-lookback:]

        if len(prices) < 10:
            raise ValueError("Need at least 10 data points to train")

        metrics_model = factory()
        metrics = self._evaluate_model(metrics_model, prices)

        trained_model = factory()
        trained_model.fit(prices)

        version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        artifact_path = self._artifact_path(symbol, model_name, version)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with open(artifact_path, "wb") as fh:
            pickle.dump(trained_model, fh)

        train_start = historical[max(0, len(historical) - len(prices))]["date"]
        train_end = historical[-1]["date"]
        hyperparams = {
            "mode": mode,
            "lookback": lookback,
        }

        self.db.insert_model_version(
            symbol=symbol,
            model_name=model_name,
            version=version,
            status="ready",
            train_start=train_start,
            train_end=train_end,
            metrics=metrics,
            hyperparams=hyperparams,
            artifact_path=str(artifact_path),
            activate=activate,
        )

        LOGGER.info(
            "Trained %s model for %s (version %s)",
            model_name,
            symbol,
            version,
        )

        return {
            "symbol": symbol,
            "model": model_name,
            "version": version,
            "metrics": metrics,
            "artifact_path": str(artifact_path),
        }

    def _evaluate_model(self, model, data: np.ndarray) -> Dict:
        if len(data) < 14:
            model.fit(data)
            return {
                "rmse": None,
                "mae": None,
                "mape": None,
                "train_samples": len(data),
                "test_samples": 0,
            }
        test_size = max(3, len(data) // 5)
        train = data[:-test_size]
        test = data[-test_size:]
        metrics = model.evaluate(train, test)
        return metrics

    def load_active_model(self, symbol: str, model_name: str):
        version = self.db.get_active_model_version(symbol, model_name)
        if not version:
            return None, None
        path = version.get("artifact_path")
        if not path or not os.path.exists(path):
            LOGGER.warning("Artifact missing for %s/%s version %s", symbol, model_name, version.get("version"))
            return None, version
        with open(path, "rb") as fh:
            model = pickle.load(fh)
        return model, version

    def predict_with_model(self, model, prices: np.ndarray, steps: int):
        if model is None:
            raise ValueError("Model not loaded")
        signature = inspect.signature(model.predict)
        params = list(signature.parameters.keys())
        if len(params) >= 2:
            predictions, confidence = model.predict(prices, steps=steps)
        else:
            predictions, confidence = model.predict(steps=steps)
        return predictions, confidence

    def get_available_models(self):
        return list(self.factories.keys())
