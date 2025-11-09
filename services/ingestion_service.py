"""Data ingestion utilities for adaptive pipeline."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import yfinance as yf

from .config_service import CONFIG

LOGGER = logging.getLogger(__name__)


class IngestionService:
    """Fetches fresh OHLCV data and stores it in the database."""

    def __init__(self, db):
        self.db = db

    def _download_symbol(self, symbol: str, days: int) -> pd.DataFrame:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval="1h" if "-USD" in symbol else "1d")
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        df = df.reset_index().rename(
            columns={
                "Datetime": "date",
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["return_1d"] = df["close"].pct_change().fillna(0)
        df["sma_5"] = df["close"].rolling(window=5).mean().fillna(method="bfill")
        df["sma_20"] = df["close"].rolling(window=20).mean().fillna(method="bfill")
        df["vol_5d"] = df["return_1d"].rolling(window=5).std().fillna(0)
        return df

    def _records_from_df(self, df: pd.DataFrame) -> List[Dict]:
        return [
            {
                "date": row.date,
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": int(row.volume or 0),
                "return_1d": float(row.return_1d),
                "vol_5d": float(row.vol_5d),
                "sma_5": float(row.sma_5),
                "sma_20": float(row.sma_20),
            }
            for row in df.itertuples(index=False)
        ]

    def ingest(self, symbol: str, days: int | None = None) -> Dict[str, int | str]:
        """Download and persist data for a symbol."""
        window_days = days or CONFIG.ingestion_window_days
        try:
            df = self._download_symbol(symbol, window_days)
            records = self._records_from_df(df)
            self.db.insert_historical_data(symbol, records)
            summary = {"symbol": symbol, "rows": len(records), "status": "ok"}
            self.db.insert_ingestion_event(symbol, "yfinance", len(records), "ok", "")
            LOGGER.info("Ingested %s rows for %s", len(records), symbol)
            return summary
        except Exception as exc:  # pragma: no cover - logging path
            message = str(exc)
            LOGGER.error("Ingestion failed for %s: %s", symbol, message)
            self.db.insert_ingestion_event(symbol, "yfinance", 0, "failed", message)
            raise

    def ingest_all(self) -> List[Dict[str, int | str]]:
        results: List[Dict[str, int | str]] = []
        for symbol in CONFIG.ingest_symbols:
            try:
                results.append(self.ingest(symbol))
            except Exception as exc:
                results.append({"symbol": symbol, "rows": 0, "status": "failed", "message": str(exc)})
        return results
