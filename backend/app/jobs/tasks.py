"""Scheduled job stubs."""

import logging

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.order import QueuedTrade
from app.models.portfolio import Portfolio
from app.schemas.trade import OrderCreate
from app.services.ai_decision_service import ai_decision_service
from app.services.benchmark_service import benchmark_service
from app.services.market_schedule import market_schedule_service
from app.services.news_service import news_service
from app.services.report_service import report_service
from app.services.trade_service import trade_service

logger = logging.getLogger(__name__)


def run_intraday_analysis() -> None:
    logger.info("Running intraday analysis cycle.")
    if not market_schedule_service.is_market_open():
        return
    with SessionLocal() as db:
        news_service.ingest_latest(db)
        portfolios = db.scalars(select(Portfolio).where(Portfolio.is_active.is_(True))).all()
        for portfolio in portfolios:
            ai_decision_service.run_analysis(db, portfolio.id)
            benchmark_service.refresh_for_portfolio(db, portfolio)


def run_evening_scan() -> None:
    logger.info("Running limited after-hours scan.")
    with SessionLocal() as db:
        news_service.ingest_latest(db)


def publish_daily_reports() -> None:
    logger.info("Publishing scheduled daily reports at approximately 3:10 PM Central.")
    if not market_schedule_service.is_trading_day():
        return
    with SessionLocal() as db:
        portfolios = db.scalars(select(Portfolio).where(Portfolio.is_active.is_(True))).all()
        for portfolio in portfolios:
            report_service.generate_daily_report(db, portfolio.id)


def execute_queued_market_open_orders() -> None:
    logger.info("Executing queued next-open paper orders.")
    if not market_schedule_service.is_market_open():
        return
    with SessionLocal() as db:
        queued = db.scalars(select(QueuedTrade).where(QueuedTrade.execute_on_market_open.is_(True))).all()
        for item in queued:
            try:
                order = OrderCreate(
                    portfolio_id=item.portfolio_id,
                    ticker=item.ticker,
                    side=item.side,
                    quantity=item.quantity,
                )
                trade_service.create_order(db, item.portfolio.user_id, order)
                db.delete(item)
                db.commit()
            except Exception as exc:
                logger.warning("Queued trade %s failed: %s", item.id, exc)
