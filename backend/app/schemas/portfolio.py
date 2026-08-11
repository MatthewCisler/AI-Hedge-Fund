"""Portfolio schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampedResponse


class PortfolioRuleBase(BaseModel):
    max_position_size_pct: float = Field(default=10.0, ge=1, le=100)
    max_daily_trades: int = Field(default=3, ge=0, le=100)
    max_weekly_trades: int = Field(default=15, ge=0, le=500)
    etf_allowed: bool = True
    rebalance_threshold: float = Field(default=5.0, ge=0)
    sector_concentration_limit: float = Field(default=25.0, ge=1, le=100)
    cash_reserve_pct: float = Field(default=5.0, ge=0, le=100)
    minimum_liquidity_volume: int = Field(default=500000, ge=0)
    allow_queued_after_hours: bool = True
    cooldown_minutes_per_ticker: int = Field(default=60, ge=0)
    allowed_tickers: list[str] = Field(default_factory=list)
    blocked_tickers: list[str] = Field(default_factory=list)
    aggressiveness: float = Field(default=50.0, ge=0, le=100)
    after_hours_news_scanning: bool = True


class PortfolioRuleUpdate(PortfolioRuleBase):
    pass


class PortfolioRuleResponse(PortfolioRuleBase, TimestampedResponse):
    portfolio_id: int


class PortfolioCreate(BaseModel):
    name: str
    initial_investment: float = Field(gt=0)
    risk_profile: str = Field(pattern="^(safe|balanced|risky|custom)$")
    benchmark_symbol: str = Field(default="SPY", pattern="^(SPY|QQQ|DIA|60_40)$")
    rules: PortfolioRuleUpdate | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    risk_profile: str | None = Field(default=None, pattern="^(safe|balanced|risky|custom)$")
    is_active: bool | None = None
    benchmark_symbol: str | None = Field(default=None, pattern="^(SPY|QQQ|DIA|60_40)$")


class PortfolioSummary(ORMModel):
    id: int
    name: str
    initial_investment: float
    cash_balance: float
    current_value: float
    risk_profile: str
    is_active: bool
    benchmark_symbol: str = "SPY"
    daily_gain_loss: float = 0
    total_return_pct: float = 0


class PositionResponse(ORMModel):
    id: int
    ticker: str
    asset_name: str | None
    asset_type: str
    quantity: float
    average_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    sector: str | None


class PortfolioQueuedTradeResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    side: str
    quantity: float
    reason: str
    execute_on_market_open: bool


class PortfolioTradeResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    side: str
    quantity: float
    fill_price: float
    realized_pnl: float | None
    notes: str | None


class PortfolioAIDecisionResponse(ORMModel):
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
    created_at: datetime
    input_snapshot: dict | None = None
    rules_result: dict | None = None


class PortfolioDailyReportResponse(ORMModel):
    id: int
    portfolio_id: int
    report_date: date
    csv_path: str | None
    summary: dict


class PortfolioBenchmarkResponse(ORMModel):
    id: int
    portfolio_id: int
    benchmark_symbol: str
    snapshot_date: date
    initial_value: float
    current_value: float
    daily_return_pct: float
    total_return_pct: float


class PortfolioDetail(PortfolioSummary):
    rules: PortfolioRuleResponse | None
    positions: list[PositionResponse]
    queued_trades: list[PortfolioQueuedTradeResponse] = Field(default_factory=list)
    trades: list[PortfolioTradeResponse] = Field(default_factory=list)
    ai_decisions: list[PortfolioAIDecisionResponse] = Field(default_factory=list)
    daily_reports: list[PortfolioDailyReportResponse] = Field(default_factory=list)
    benchmark_snapshots: list[PortfolioBenchmarkResponse] = Field(default_factory=list)


class PortfolioActionResponse(BaseModel):
    status: str
    message: str
    demo_mode: bool = True
    result: dict | list[dict] | None = None
