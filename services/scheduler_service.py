"""Background scheduler for continuous learning pipeline."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .adaptive_service import AdaptiveLearningService
from .config_service import CONFIG
from .evaluation_service import EvaluationService
from .ingestion_service import IngestionService
from .portfolio_service import PortfolioService

LOGGER = logging.getLogger(__name__)


class PipelineScheduler:
    def __init__(self, db):
        self.db = db
        self.scheduler: BackgroundScheduler | None = None
        self.ingestion = IngestionService(db)
        self.evaluation = EvaluationService(db)
        self.adaptive = AdaptiveLearningService(db)
        self.portfolio = PortfolioService(db)

    def start(self):
        if not CONFIG.scheduler_enabled:
            LOGGER.info("Scheduler disabled via configuration")
            return
        if self.scheduler:
            return
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._run_ingestion, IntervalTrigger(hours=6), id='ingestion')
        self.scheduler.add_job(self._run_training, IntervalTrigger(hours=12), id='training')
        self.scheduler.add_job(self._run_evaluation, IntervalTrigger(hours=4), id='evaluation')
        self.scheduler.add_job(self._run_portfolio, IntervalTrigger(hours=6), id='portfolio')
        self.scheduler.start()
        LOGGER.info("Background scheduler started")

    def shutdown(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            LOGGER.info("Background scheduler stopped")

    def _run_ingestion(self):
        try:
            self.ingestion.ingest_all()
        except Exception as exc:  # pragma: no cover - log path only
            LOGGER.exception("Ingestion job failed: %s", exc)

    def _run_training(self):
        for symbol in CONFIG.ingest_symbols:
            for model_name in self.adaptive.get_available_models():
                try:
                    self.adaptive.train(symbol=symbol, model_name=model_name, mode='update', activate=True)
                except Exception as exc:
                    LOGGER.warning("Training skipped for %s/%s: %s", symbol, model_name, exc)

    def _run_evaluation(self):
        try:
            self.evaluation.evaluate_pending()
        except Exception as exc:
            LOGGER.exception("Evaluation job failed: %s", exc)

    def _run_portfolio(self):
        try:
            self.portfolio.run_auto_strategy()
        except Exception as exc:
            LOGGER.exception("Portfolio job failed: %s", exc)
