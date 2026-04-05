"""Scheduled job stubs."""

import logging

from app.services.ai_service import ai_service
from app.services.news_service import news_service

logger = logging.getLogger(__name__)


def run_intraday_analysis() -> None:
    logger.info("Running intraday analysis cycle.")
    news_items = news_service.fetch_latest()
    ai_service.analyze(
        portfolio_state={"mode": "intraday"},
        candidate_universe=["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
        recent_news=[item.__dict__ for item in news_items],
        price_context={"window": "1d"},
    )


def run_evening_scan() -> None:
    logger.info("Running limited after-hours scan.")


def publish_daily_reports() -> None:
    logger.info("Publishing scheduled daily reports at approximately 3:10 PM Central.")


def execute_queued_market_open_orders() -> None:
    logger.info("Executing queued next-open paper orders.")
