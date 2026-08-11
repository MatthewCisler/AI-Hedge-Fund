"""Dashboard schemas."""

from datetime import date, datetime

from app.schemas.common import ORMModel

from app.schemas.portfolio import PortfolioSummary
from app.schemas.trade import OrderResponse, QueuedTradeResponse


class NewsArticleResponse(ORMModel):
    id: int
    source: str
    headline: str
    url: str
    published_at: datetime
    summary: str | None
    inferred_tickers: list[str] | None


class AIDecisionResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    action_suggestion: str
    confidence_score: float
    explanation: str
    provider: str = "legacy"
    model_name: str | None = None
    analysis_status: str = "completed"
    failure_category: str | None = None
    analysis_run_id: str | None = None
    input_snapshot: dict | None = None
    rules_result: dict | None = None
    created_at: datetime


class DailyReportSummary(ORMModel):
    id: int
    portfolio_id: int
    report_date: date
    csv_path: str | None
    summary: dict


class BenchmarkSnapshotResponse(ORMModel):
    id: int
    portfolio_id: int
    benchmark_symbol: str
    snapshot_date: date
    initial_value: float
    current_value: float
    daily_return_pct: float
    total_return_pct: float


class DashboardResponse(ORMModel):
    portfolios: list[PortfolioSummary]
    queued_trades: list[QueuedTradeResponse]
    recent_orders: list[OrderResponse]
    recent_news: list[NewsArticleResponse]
    recent_ai_decisions: list[AIDecisionResponse]
    latest_reports: list[DailyReportSummary]
    benchmarks: list[BenchmarkSnapshotResponse]
