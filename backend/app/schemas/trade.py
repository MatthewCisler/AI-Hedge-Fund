"""Order and trade schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class OrderCreate(BaseModel):
    portfolio_id: int
    ticker: str = Field(min_length=1, max_length=16)
    side: str = Field(pattern="^(buy|sell)$")
    quantity: float = Field(gt=0)
    ai_decision_id: int | None = None


class OrderResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    side: str
    quantity: float
    order_type: str
    status: str
    requested_price: float | None
    broker_order_id: str | None
    rejection_reason: str | None
    ai_decision_id: int | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None


class QueuedTradeResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    side: str
    quantity: float
    reason: str
    execute_on_market_open: bool


class TradeResponse(ORMModel):
    id: int
    portfolio_id: int
    ticker: str
    side: str
    quantity: float
    fill_price: float
    realized_pnl: float | None
    notes: str | None
