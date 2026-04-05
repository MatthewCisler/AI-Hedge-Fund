"""Portfolio CRUD and defaults."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.portfolio import Portfolio, PortfolioRule
from app.schemas.portfolio import PortfolioCreate, PortfolioRuleUpdate
from app.services.defaults import RISK_PROFILE_DEFAULTS


class PortfolioService:
    def list_for_user(self, db: Session, user_id: int) -> list[Portfolio]:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.rules), selectinload(Portfolio.positions))
            .order_by(Portfolio.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_for_user(self, db: Session, user_id: int, portfolio_id: int) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id, Portfolio.id == portfolio_id)
            .options(selectinload(Portfolio.rules), selectinload(Portfolio.positions))
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


portfolio_service = PortfolioService()
