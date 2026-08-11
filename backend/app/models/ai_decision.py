"""AI analysis records."""

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

AI_ACTIONS = ("buy", "sell", "hold", "rebalance")


class AIDecision(TimestampMixin, Base):
    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    action_suggestion: Mapped[str] = mapped_column(Enum(*AI_ACTIONS, name="ai_action"))
    confidence_score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(40), default="legacy")
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(40), default="completed")
    failure_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    analysis_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rules_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    portfolio = relationship("Portfolio", back_populates="ai_decisions")
