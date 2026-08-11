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


def run_intraday_analysis(*, force: bool = False, user_id: int | None = None) -> dict:
    logger.info("Running intraday analysis cycle.")
    if not force and not market_schedule_service.is_market_open():
        return {"status": "skipped", "reason": "market_closed", "portfolios": 0}
    analyzed = 0
    with SessionLocal() as db:
        news_service.ingest_latest(db)
        stmt = select(Portfolio).where(Portfolio.is_active.is_(True))
        if user_id is not None:
            stmt = stmt.where(Portfolio.user_id == user_id)
        portfolios = db.scalars(stmt).all()
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


def publish_daily_reports(*, force: bool = False, user_id: int | None = None) -> dict:
    logger.info("Publishing scheduled daily reports at approximately 3:10 PM Central.")
    if not force and not market_schedule_service.is_trading_day():
        return {"status": "skipped", "reason": "non_trading_day", "reports": 0}
    reports = 0
    with SessionLocal() as db:
        stmt = select(Portfolio).where(Portfolio.is_active.is_(True))
        if user_id is not None:
            stmt = stmt.where(Portfolio.user_id == user_id)
        portfolios = db.scalars(stmt).all()
        for portfolio in portfolios:
            report_service.generate_daily_report(db, portfolio.id)
            reports += 1
    return {"status": "ok", "reports": reports}


def execute_queued_market_open_orders(*, force: bool = False, user_id: int | None = None) -> dict:
    logger.info("Executing queued next-open paper orders.")
    if not force and not market_schedule_service.is_market_open():
        return {"status": "skipped", "reason": "market_closed", "orders": 0}
    executed = 0
    failed = 0
    with SessionLocal() as db:
        stmt = select(QueuedTrade).where(QueuedTrade.execute_on_market_open.is_(True))
        if user_id is not None:
            stmt = stmt.join(Portfolio, Portfolio.id == QueuedTrade.portfolio_id).where(Portfolio.user_id == user_id)
        queued = db.scalars(stmt).all()
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


def synchronize_broker_orders(*, user_id: int | None = None) -> dict:
    """Poll pending Alpaca paper orders and apply only confirmed complete fills."""
    with SessionLocal() as db:
        return {"status": "ok", **trade_service.synchronize_orders(db, user_id=user_id)}
