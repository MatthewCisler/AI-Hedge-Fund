"""Portfolio CRUD and defaults."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import QueuedTrade
from app.models.portfolio import Portfolio, PortfolioRule
from app.schemas.portfolio import PortfolioCreate, PortfolioRuleUpdate, PortfolioUpdate
from app.services.defaults import RISK_PROFILE_DEFAULTS


class PortfolioService:
    def list_for_user(self, db: Session, user_id: int) -> list[Portfolio]:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.rules), selectinload(Portfolio.positions), selectinload(Portfolio.benchmark_snapshots))
            .order_by(Portfolio.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_for_user(self, db: Session, user_id: int, portfolio_id: int) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id, Portfolio.id == portfolio_id)
            .options(
                selectinload(Portfolio.rules),
                selectinload(Portfolio.positions),
                selectinload(Portfolio.queued_trades),
                selectinload(Portfolio.trades),
                selectinload(Portfolio.ai_decisions),
                selectinload(Portfolio.daily_reports),
                selectinload(Portfolio.benchmark_snapshots),
            )
        )
        return db.scalar(stmt)

    def create(self, db: Session, user_id: int, payload: PortfolioCreate) -> Portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name=payload.name,
            initial_investment=payload.initial_investment,
            cash_balance=payload.initial_investment,
            current_value=payload.initial_investment,
            risk_profile=payload.risk_profile,
            benchmark_symbol=payload.benchmark_symbol,
        )
        db.add(portfolio)
        db.flush()

        rule_values = RISK_PROFILE_DEFAULTS[payload.risk_profile].copy()
        if payload.rules:
            rule_values.update(payload.rules.model_dump())
        rules = PortfolioRule(portfolio_id=portfolio.id, **rule_values)
        db.add(rules)
        db.commit()
        db.refresh(portfolio)
        return self.get_for_user(db, user_id, portfolio.id)

    def update(self, db: Session, user_id: int, portfolio_id: int, payload: PortfolioUpdate) -> Portfolio:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(portfolio, field, value)
        db.commit()
        return self.get_for_user(db, user_id, portfolio_id)

    def get_rules(self, db: Session, user_id: int, portfolio_id: int) -> PortfolioRule:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio or rules not found.")
        return portfolio.rules

    def update_rules(
        self, db: Session, user_id: int, portfolio_id: int, payload: PortfolioRuleUpdate
    ) -> PortfolioRule:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio or rules not found.")

        for field, value in payload.model_dump().items():
            setattr(portfolio.rules, field, value)
        db.commit()
        db.refresh(portfolio.rules)
        return portfolio.rules

    def set_active(self, db: Session, user_id: int, portfolio_id: int, is_active: bool) -> Portfolio:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found.")
        portfolio.is_active = is_active
        db.commit()
        return self.get_for_user(db, user_id, portfolio_id)

    def clear_queued_trades(self, db: Session, user_id: int, portfolio_id: int) -> int:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found.")
        result = db.execute(delete(QueuedTrade).where(QueuedTrade.portfolio_id == portfolio_id))
        db.commit()
        return int(result.rowcount or 0)

    def queue_demo_rebalance(self, db: Session, user_id: int, portfolio_id: int) -> QueuedTrade:
        portfolio = self.get_for_user(db, user_id, portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found.")
        trade = QueuedTrade(
            portfolio_id=portfolio_id,
            ticker=portfolio.benchmark_symbol if portfolio.benchmark_symbol != "60_40" else "SPY",
            side="buy",
            quantity=1,
            reason="Demo rebalance queued by portfolio control. Paper-trading only.",
            execute_on_market_open=True,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade


portfolio_service = PortfolioService()
