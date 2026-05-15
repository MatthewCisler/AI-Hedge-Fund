"""Benchmark tracking models."""

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

BENCHMARK_SYMBOLS = ("SPY", "QQQ", "DIA", "60_40")


class BenchmarkSnapshot(TimestampMixin, Base):
    __tablename__ = "benchmark_snapshots"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "benchmark_symbol", "snapshot_date", name="uq_benchmark_snapshot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    benchmark_symbol: Mapped[str] = mapped_column(String(16), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    initial_value: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float)
    daily_return_pct: Mapped[float] = mapped_column(Float, default=0)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0)

    portfolio = relationship("Portfolio", back_populates="benchmark_snapshots")
