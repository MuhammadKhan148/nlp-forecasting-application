"""Central configuration helpers for services."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def _list_from_env(name: str, default: str | None = None) -> List[str]:
    raw = os.environ.get(name, default or "")
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class ServiceConfig:
    ingest_symbols: List[str]
    ingestion_window_days: int
    scheduler_enabled: bool
    adaptive_default_horizon: int
    model_store_dir: str
    portfolio_initial_cash: float
    forecast_error_window: int

    @classmethod
    def load(cls) -> "ServiceConfig":
        ingest_symbols = _list_from_env("INGEST_SYMBOLS", "AAPL,MSFT,BTC-USD")
        ingestion_window_days = int(os.environ.get("INGEST_WINDOW_DAYS", "14"))
        scheduler_enabled = os.environ.get("ENABLE_SCHEDULER", "1") == "1"
        adaptive_default_horizon = int(os.environ.get("ADAPTIVE_DEFAULT_HOURS", "24"))
        model_store_dir = os.environ.get("MODEL_STORE_DIR", "models_store")
        portfolio_initial_cash = float(os.environ.get("PORTFOLIO_INITIAL_CASH", "100000"))
        forecast_error_window = int(os.environ.get("FORECAST_ERROR_WINDOW", "30"))
        return cls(
            ingest_symbols=ingest_symbols,
            ingestion_window_days=ingestion_window_days,
            scheduler_enabled=scheduler_enabled,
            adaptive_default_horizon=adaptive_default_horizon,
            model_store_dir=model_store_dir,
            portfolio_initial_cash=portfolio_initial_cash,
            forecast_error_window=forecast_error_window,
        )


CONFIG = ServiceConfig.load()
