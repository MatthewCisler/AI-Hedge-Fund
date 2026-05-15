"""Deterministic trade validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.market_schedule import market_schedule_service


@dataclass
class RuleValidationResult:
    approved: bool
    queue_for_next_open: bool
    reasons: list[str]


class RulesEngineService:
    def validate_trade_idea(
        self,
        *,
        portfolio: object,
        rules: object,
        ticker: str,
        side: str,
        quantity: float,
        estimated_price: float,
        average_volume: int,
        asset_type: str = "stock",
        existing_position_value: float = 0,
        daily_trade_count: int = 0,
        recent_trade_exists: bool = False,
    ) -> RuleValidationResult:
        reasons: list[str] = []
        queue_for_next_open = False

        if not ticker.replace(".", "").replace("-", "").isalnum() or not ticker.isupper():
            reasons.append("Ticker must be an uppercase U.S. stock or ETF symbol.")

        if side not in {"buy", "sell"}:
            reasons.append("Only buy and sell market orders are supported.")

        if not market_schedule_service.is_market_open():
            if getattr(rules, "allow_queued_after_hours", False):
                queue_for_next_open = True
                reasons.append("Market closed. Trade can be queued for next open.")
            else:
                reasons.append("Market closed and after-hours queueing is disabled.")

        if average_volume < getattr(rules, "minimum_liquidity_volume", 0):
            reasons.append("Liquidity rule failed.")

        if asset_type == "etf" and not getattr(rules, "etf_allowed", True):
            reasons.append("ETF trades are disabled for this portfolio.")

        if daily_trade_count >= getattr(rules, "max_daily_trades", 0):
            reasons.append("Maximum daily trade count reached.")

        projected_trade_value = estimated_price * quantity
        portfolio_value = float(getattr(portfolio, "current_value", 0) or 0) or float(
            getattr(portfolio, "initial_investment", 0)
        )
        max_position_value = portfolio_value * (getattr(rules, "max_position_size_pct", 0) / 100)
        if existing_position_value + projected_trade_value > max_position_value:
            reasons.append("Max position size exceeded.")

        if side == "buy" and projected_trade_value > float(getattr(portfolio, "cash_balance", 0)):
            reasons.append("Insufficient cash for buy order.")

        if recent_trade_exists:
            reasons.append("Cooldown rule blocked rapid duplicate trade.")

        approved = not reasons or (queue_for_next_open and reasons == ["Market closed. Trade can be queued for next open."])
        return RuleValidationResult(approved=approved, queue_for_next_open=queue_for_next_open, reasons=reasons)

    def cooldown_cutoff(self, minutes: int) -> datetime:
        return market_schedule_service.now_ct() - timedelta(minutes=minutes)


rules_engine_service = RulesEngineService()
