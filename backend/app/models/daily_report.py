"""Daily report models."""

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DailyReport(TimestampMixin, Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    csv_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio = relationship("Portfolio", back_populates="daily_reports")
    rows = relationship("ReportRow", back_populates="report", cascade="all, delete-orphan")


class ReportRow(TimestampMixin, Base):
    __tablename__ = "report_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("daily_reports.id", ondelete="CASCADE"), index=True)
    section: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(String(255))
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    report = relationship("DailyReport", back_populates="rows")
