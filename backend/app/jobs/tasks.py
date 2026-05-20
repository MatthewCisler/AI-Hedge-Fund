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


def run_intraday_analysis(*, force: bool = False) -> dict:
    logger.info("Running intraday analysis cycle.")
    if not force and not market_schedule_service.is_market_open():
        return {"status": "skipped", "reason": "market_closed", "portfolios": 0}
    analyzed = 0
    with SessionLocal() as db:
        news_service.ingest_latest(db)
        portfolios = db.scalars(select(Portfolio).where(Portfolio.is_active.is_(True))).all()
        for portfolio in portfolios:
            ai_decision_service.run_analysis(db, portfolio.id)
            benchmark_service.refresh_for_portfolio(db, portfolio)
            analyzed += 1
    return {"status": "ok", "portfolios": analyzed}


def run_evening_scan() -> dict:
    logger.info("Running limited after-hours scan.")
    with SessionLocal() as db:
        articles = news_service.ingest_latest(db)
    return {"status": "ok", "articles_ingested": len(articles)}


def publish_daily_reports(*, force: bool = False) -> dict:
    logger.info("Publishing scheduled daily reports at approximately 3:10 PM Central.")
    if not force and not market_schedule_service.is_trading_day():
        return {"status": "skipped", "reason": "non_trading_day", "reports": 0}
    reports = 0
    with SessionLocal() as db:
        portfolios = db.scalars(select(Portfolio).where(Portfolio.is_active.is_(True))).all()
        for portfolio in portfolios:
            report_service.generate_daily_report(db, portfolio.id)
            reports += 1
    return {"status": "ok", "reports": reports}


def execute_queued_market_open_orders(*, force: bool = False) -> dict:
    logger.info("Executing queued next-open paper orders.")
    if not force and not market_schedule_service.is_market_open():
        return {"status": "skipped", "reason": "market_closed", "orders": 0}
    executed = 0
    failed = 0
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
                executed += 1
            except Exception as exc:
                failed += 1
                logger.warning("Queued trade %s failed: %s", item.id, exc)
    return {"status": "ok", "orders": executed, "failed": failed}
