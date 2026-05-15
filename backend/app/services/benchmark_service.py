"""Benchmark tracking for AI portfolio comparisons."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark import BENCHMARK_SYMBOLS, BenchmarkSnapshot
from app.models.portfolio import Portfolio
from app.services.broker_service import broker_service


class BenchmarkService:
    symbols = BENCHMARK_SYMBOLS

    def refresh_for_portfolio(
        self, db: Session, portfolio: Portfolio, snapshot_date: date | None = None
    ) -> list[BenchmarkSnapshot]:
        snapshot_date = snapshot_date or date.today()
        snapshots: list[BenchmarkSnapshot] = []
        portfolio_total_return = self._return_pct(float(portfolio.current_value), float(portfolio.initial_investment))
        for symbol in self.symbols:
            current_value = self._estimate_benchmark_value(portfolio, symbol, portfolio_total_return)
            snapshot = db.scalar(
                select(BenchmarkSnapshot).where(
                    BenchmarkSnapshot.portfolio_id == portfolio.id,
                    BenchmarkSnapshot.benchmark_symbol == symbol,
                    BenchmarkSnapshot.snapshot_date == snapshot_date,
                )
            )
            if not snapshot:
                snapshot = BenchmarkSnapshot(
                    portfolio_id=portfolio.id,
                    benchmark_symbol=symbol,
                    snapshot_date=snapshot_date,
                    initial_value=float(portfolio.initial_investment),
                    current_value=current_value,
                )
                db.add(snapshot)
            previous = self._previous_snapshot(db, portfolio.id, symbol, snapshot_date)
            snapshot.current_value = current_value
            snapshot.total_return_pct = self._return_pct(current_value, snapshot.initial_value)
            snapshot.daily_return_pct = self._return_pct(current_value, previous.current_value) if previous else 0
            snapshots.append(snapshot)
        db.commit()
        for snapshot in snapshots:
            db.refresh(snapshot)
        return snapshots

    def list_for_portfolio(self, db: Session, portfolio_id: int) -> list[BenchmarkSnapshot]:
        return list(
            db.scalars(
                select(BenchmarkSnapshot)
                .where(BenchmarkSnapshot.portfolio_id == portfolio_id)
                .order_by(BenchmarkSnapshot.snapshot_date.desc(), BenchmarkSnapshot.benchmark_symbol)
            ).all()
        )

    def latest_for_portfolio(self, db: Session, portfolio_id: int) -> list[BenchmarkSnapshot]:
        latest_date = db.scalar(
            select(BenchmarkSnapshot.snapshot_date)
            .where(BenchmarkSnapshot.portfolio_id == portfolio_id)
            .order_by(BenchmarkSnapshot.snapshot_date.desc())
            .limit(1)
        )
        if not latest_date:
            return []
        return list(
            db.scalars(
                select(BenchmarkSnapshot)
                .where(
                    BenchmarkSnapshot.portfolio_id == portfolio_id,
                    BenchmarkSnapshot.snapshot_date == latest_date,
                )
                .order_by(BenchmarkSnapshot.benchmark_symbol)
            ).all()
        )

    def _estimate_benchmark_value(self, portfolio: Portfolio, symbol: str, portfolio_return: float) -> float:
        # Without historical benchmark basis stored at portfolio creation, seed a conservative
        # deterministic comparison that can be replaced by a market-data-backed calculator.
        baseline_returns = {"SPY": 0.0015, "QQQ": 0.002, "DIA": 0.001, "60_40": 0.0008}
        price = broker_service.latest_price(symbol if symbol != "60_40" else "SPY")
        if price:
            baseline = baseline_returns[symbol] + min(max(portfolio_return / 100, -0.2), 0.2) * 0.15
        else:
            baseline = baseline_returns[symbol]
        return float(portfolio.initial_investment) * (1 + baseline)

    def _previous_snapshot(
        self, db: Session, portfolio_id: int, symbol: str, snapshot_date: date
    ) -> BenchmarkSnapshot | None:
        return db.scalar(
            select(BenchmarkSnapshot)
            .where(
                BenchmarkSnapshot.portfolio_id == portfolio_id,
                BenchmarkSnapshot.benchmark_symbol == symbol,
                BenchmarkSnapshot.snapshot_date < snapshot_date,
            )
            .order_by(BenchmarkSnapshot.snapshot_date.desc())
            .limit(1)
        )

    def _return_pct(self, current: float, initial: float) -> float:
        if not initial:
            return 0
        return ((current - initial) / initial) * 100


benchmark_service = BenchmarkService()
