"""Daily report generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_decision import AIDecision
from app.models.daily_report import DailyReport, ReportRow
from app.models.news_article import NewsArticle
from app.models.order import QueuedTrade, Trade
from app.models.portfolio import Portfolio
from app.services.benchmark_service import benchmark_service


class ReportService:
    def generate_daily_report(self, db: Session, portfolio_id: int, report_date: date | None = None) -> DailyReport:
        report_date = report_date or date.today()
        portfolio = db.scalar(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .options(
                selectinload(Portfolio.positions),
                selectinload(Portfolio.trades),
                selectinload(Portfolio.ai_decisions),
            )
        )
        if not portfolio:
            raise ValueError("Portfolio not found.")

        benchmarks = benchmark_service.refresh_for_portfolio(db, portfolio, report_date)
        previous_report = db.scalar(
            select(DailyReport)
            .where(DailyReport.portfolio_id == portfolio.id, DailyReport.report_date < report_date)
            .order_by(DailyReport.report_date.desc())
            .limit(1)
        )
        previous_value = (
            float(previous_report.summary.get("current_portfolio_value", portfolio.initial_investment))
            if previous_report
            else float(portfolio.initial_investment)
        )
        current_value = float(portfolio.current_value)
        initial = float(portfolio.initial_investment)
        summary = {
            "initial_investment": initial,
            "current_portfolio_value": current_value,
            "daily_return_pct": self._return_pct(current_value, previous_value),
            "total_return_pct": self._return_pct(current_value, initial),
            "cash_balance": float(portfolio.cash_balance),
            "benchmarks": {
                item.benchmark_symbol: {
                    "current_value": item.current_value,
                    "daily_return_pct": item.daily_return_pct,
                    "total_return_pct": item.total_return_pct,
                    "ai_beating": self._return_pct(current_value, initial) > item.total_return_pct,
                }
                for item in benchmarks
            },
        }

        report = DailyReport(
            portfolio_id=portfolio.id,
            report_date=report_date,
            summary=summary,
            narrative="Generated daily educational paper-trading summary.",
        )
        db.add(report)
        db.flush()

        rows = [
            ReportRow(report_id=report.id, section="summary", label=label, value=str(value), numeric_value=float(value))
            for label, value in summary.items()
            if isinstance(value, int | float)
        ]
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="holdings",
                label=position.ticker,
                value=(
                    f"{position.quantity} shares @ {position.market_price}; "
                    f"{self._allocation_pct(position.market_value, current_value):.2f}% allocation"
                ),
                numeric_value=position.market_value,
            )
            for position in portfolio.positions
        )
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="benchmarks",
                label=benchmark.benchmark_symbol,
                value=f"{benchmark.total_return_pct:.2f}% total return",
                numeric_value=benchmark.total_return_pct,
            )
            for benchmark in benchmarks
        )
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="trades_today",
                label=f"{trade.side.upper()} {trade.ticker}",
                value=f"{trade.quantity} @ {trade.fill_price}",
                numeric_value=trade.quantity * trade.fill_price,
            )
            for trade in self._trades_for_day(db, portfolio.id, report_date)
        )
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="queued_trades",
                label=f"{trade.side.upper()} {trade.ticker}",
                value=trade.reason,
                numeric_value=trade.quantity,
            )
            for trade in db.scalars(select(QueuedTrade).where(QueuedTrade.portfolio_id == portfolio.id)).all()
        )
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="ai_explanations",
                label=f"{decision.action_suggestion.upper()} {decision.ticker}",
                value=decision.explanation[:255],
                numeric_value=decision.confidence_score,
            )
            for decision in portfolio.ai_decisions[-10:]
        )
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="news_used",
                label=article.source,
                value=article.headline[:255],
                numeric_value=None,
            )
            for article in db.scalars(select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(10)).all()
        )
        db.add_all(rows)
        db.flush()

        output_dir = Path("generated_reports")
        output_dir.mkdir(exist_ok=True)
        csv_path = output_dir / f"portfolio_{portfolio.id}_{report_date.isoformat()}.csv"
        pd.DataFrame(
            [{"section": row.section, "label": row.label, "value": row.value, "numeric_value": row.numeric_value} for row in rows]
        ).to_csv(csv_path, index=False)
        report.csv_path = str(csv_path)

        db.commit()
        db.refresh(report)
        return report

    def _return_pct(self, current: float, initial: float) -> float:
        if not initial:
            return 0
        return ((current - initial) / initial) * 100

    def _allocation_pct(self, market_value: float, portfolio_value: float) -> float:
        if not portfolio_value:
            return 0
        return (float(market_value) / portfolio_value) * 100

    def _trades_for_day(self, db: Session, portfolio_id: int, report_date: date) -> list[Trade]:
        return list(
            db.scalars(
                select(Trade)
                .where(Trade.portfolio_id == portfolio_id)
                .order_by(Trade.created_at.desc())
            ).all()
        )

    def list_reports(self, db: Session, user_id: int) -> list[DailyReport]:
        stmt = (
            select(DailyReport)
            .join(Portfolio, Portfolio.id == DailyReport.portfolio_id)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(DailyReport.rows))
            .order_by(DailyReport.report_date.desc())
        )
        return list(db.scalars(stmt).all())

    def get_report(self, db: Session, user_id: int, report_id: int) -> DailyReport | None:
        stmt = (
            select(DailyReport)
            .join(Portfolio, Portfolio.id == DailyReport.portfolio_id)
            .where(DailyReport.id == report_id, Portfolio.user_id == user_id)
            .options(selectinload(DailyReport.rows))
        )
        return db.scalar(stmt)


report_service = ReportService()
