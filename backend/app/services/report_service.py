"""Daily report generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.daily_report import DailyReport, ReportRow
from app.models.portfolio import Portfolio


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

        summary = {
            "initial_investment": float(portfolio.initial_investment),
            "current_portfolio_value": float(portfolio.current_value),
            "daily_gain_loss": float(portfolio.current_value) - float(portfolio.initial_investment),
            "total_gain_loss": float(portfolio.current_value) - float(portfolio.initial_investment),
            "cash_balance": float(portfolio.cash_balance),
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
        ]
        rows.extend(
            ReportRow(
                report_id=report.id,
                section="holdings",
                label=position.ticker,
                value=f"{position.quantity} shares @ {position.market_price}",
                numeric_value=position.market_value,
            )
            for position in portfolio.positions
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
