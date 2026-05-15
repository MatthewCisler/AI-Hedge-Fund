"""Portfolio-related models."""

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

RISK_PROFILES = ("safe", "balanced", "risky")


class Portfolio(TimestampMixin, Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    initial_investment: Mapped[float] = mapped_column(Numeric(14, 2))
    cash_balance: Mapped[float] = mapped_column(Numeric(14, 2))
    current_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    risk_profile: Mapped[str] = mapped_column(Enum(*RISK_PROFILES, name="risk_profile"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="portfolios")
    rules = relationship("PortfolioRule", back_populates="portfolio", uselist=False, cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    queued_trades = relationship("QueuedTrade", back_populates="portfolio", cascade="all, delete-orphan")
    ai_decisions = relationship("AIDecision", back_populates="portfolio", cascade="all, delete-orphan")
    daily_reports = relationship("DailyReport", back_populates="portfolio", cascade="all, delete-orphan")
    benchmark_snapshots = relationship("BenchmarkSnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioRule(TimestampMixin, Base):
    __tablename__ = "portfolio_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), unique=True)
    max_position_size_pct: Mapped[float] = mapped_column(Float, default=10.0)
    max_daily_trades: Mapped[int] = mapped_column(Integer, default=3)
    etf_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    rebalance_threshold: Mapped[float] = mapped_column(Float, default=5.0)
    sector_concentration_limit: Mapped[float] = mapped_column(Float, default=25.0)
    minimum_liquidity_volume: Mapped[int] = mapped_column(Integer, default=500000)
    allow_queued_after_hours: Mapped[bool] = mapped_column(Boolean, default=True)
    cooldown_minutes_per_ticker: Mapped[int] = mapped_column(Integer, default=60)

    portfolio = relationship("Portfolio", back_populates="rules")


class Position(TimestampMixin, Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    asset_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(20), default="stock")
    quantity: Mapped[float] = mapped_column(Float, default=0)
    average_cost: Mapped[float] = mapped_column(Float, default=0)
    market_price: Mapped[float] = mapped_column(Float, default=0)
    market_value: Mapped[float] = mapped_column(Float, default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)

    portfolio = relationship("Portfolio", back_populates="positions")
