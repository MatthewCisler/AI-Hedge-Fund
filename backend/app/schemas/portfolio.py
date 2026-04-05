"""Portfolio schemas."""

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampedResponse


class PortfolioRuleBase(BaseModel):
    max_position_size_pct: float = Field(default=10.0, ge=1, le=100)
    max_daily_trades: int = Field(default=3, ge=1, le=25)
    etf_allowed: bool = True
    rebalance_threshold: float = Field(default=5.0, ge=0)
    sector_concentration_limit: float = Field(default=25.0, ge=1, le=100)
    minimum_liquidity_volume: int = Field(default=500000, ge=0)
    allow_queued_after_hours: bool = True
    cooldown_minutes_per_ticker: int = Field(default=60, ge=0)


class PortfolioRuleUpdate(PortfolioRuleBase):
    pass


class PortfolioRuleResponse(PortfolioRuleBase, TimestampedResponse):
    portfolio_id: int


class PortfolioCreate(BaseModel):
    name: str
    initial_investment: float = Field(gt=0)
    risk_profile: str = Field(pattern="^(safe|balanced|risky)$")
    rules: PortfolioRuleUpdate | None = None


class PortfolioSummary(ORMModel):
    id: int
    name: str
    initial_investment: float
    cash_balance: float
    current_value: float
    risk_profile: str
    is_active: bool


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


class PortfolioDetail(PortfolioSummary):
    rules: PortfolioRuleResponse | None
    positions: list[PositionResponse]
