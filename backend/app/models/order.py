"""Order and trade models."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

ORDER_SIDES = ("buy", "sell")
ORDER_STATUSES = ("queued", "submitted", "filled", "canceled", "rejected")
ORDER_TYPES = ("market",)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    side: Mapped[str] = mapped_column(Enum(*ORDER_SIDES, name="order_side"))
    quantity: Mapped[float] = mapped_column(Float)
    order_type: Mapped[str] = mapped_column(Enum(*ORDER_TYPES, name="order_type"), default="market")
    status: Mapped[str] = mapped_column(Enum(*ORDER_STATUSES, name="order_status"), default="queued")
    broker_order_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    requested_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_decision_id: Mapped[int | None] = mapped_column(ForeignKey("ai_decisions.id"), nullable=True, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    portfolio = relationship("Portfolio", back_populates="orders")
    trade = relationship("Trade", back_populates="order", uselist=False)


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    side: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[float] = mapped_column(Float)
    fill_price: Mapped[float] = mapped_column(Float, default=0)
    realized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("Order", back_populates="trade")
    portfolio = relationship("Portfolio", back_populates="trades")


class QueuedTrade(TimestampMixin, Base):
    __tablename__ = "queued_trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    side: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    execute_on_market_open: Mapped[bool] = mapped_column(default=True)
    ai_decision_id: Mapped[int | None] = mapped_column(ForeignKey("ai_decisions.id"), nullable=True)

    portfolio = relationship("Portfolio", back_populates="queued_trades")
