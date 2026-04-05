"""Trade proposal, validation, queueing, and paper execution."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, QueuedTrade, Trade
from app.models.portfolio import Portfolio, Position
from app.schemas.trade import OrderCreate
from app.services.broker_service import broker_service
from app.services.rules_engine import rules_engine_service


class TradeService:
    def create_order(self, db: Session, user_id: int, payload: OrderCreate) -> Order | QueuedTrade:
        portfolio = db.scalar(
            select(Portfolio).where(Portfolio.id == payload.portfolio_id, Portfolio.user_id == user_id)
        )
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio not found.")

        position = db.scalar(
            select(Position).where(Position.portfolio_id == portfolio.id, Position.ticker == payload.ticker)
        )
        validation = rules_engine_service.validate_trade_idea(
            portfolio=portfolio,
            rules=portfolio.rules,
            ticker=payload.ticker,
            side=payload.side,
            quantity=payload.quantity,
            estimated_price=position.market_price if position else 100.0,
            average_volume=1_000_000,
            existing_position_value=position.market_value if position else 0,
            recent_trade_exists=False,
        )

        if validation.queue_for_next_open and validation.approved:
            queued = QueuedTrade(
                portfolio_id=portfolio.id,
                ticker=payload.ticker,
                side=payload.side,
                quantity=payload.quantity,
                reason="; ".join(validation.reasons),
                execute_on_market_open=True,
            )
            db.add(queued)
            db.commit()
            db.refresh(queued)
            return queued

        if not validation.approved:
            raise ValueError("; ".join(validation.reasons))

        order = Order(
            portfolio_id=portfolio.id,
            ticker=payload.ticker,
            side=payload.side,
            quantity=payload.quantity,
            order_type="market",
            status="submitted",
            requested_price=position.market_price if position else None,
            submitted_payload=payload.model_dump(),
        )
        db.add(order)
        db.flush()

        broker_result = broker_service.submit_market_order(
            ticker=payload.ticker, side=payload.side, quantity=payload.quantity
        )
        order.status = broker_result.status
        order.broker_order_id = broker_result.broker_order_id
        order.rejection_reason = None if broker_result.status != "rejected" else broker_result.message

        if broker_result.status == "submitted":
            trade = Trade(
                order_id=order.id,
                portfolio_id=portfolio.id,
                ticker=payload.ticker,
                side=payload.side,
                quantity=payload.quantity,
                fill_price=position.market_price if position else 100.0,
                notes="Paper trade stub execution.",
            )
            db.add(trade)

        db.commit()
        db.refresh(order)
        return order

    def list_orders(self, db: Session, user_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .where(Portfolio.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def list_queued(self, db: Session, user_id: int) -> list[QueuedTrade]:
        stmt = (
            select(QueuedTrade)
            .join(Portfolio, Portfolio.id == QueuedTrade.portfolio_id)
            .where(Portfolio.user_id == user_id)
            .order_by(QueuedTrade.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def list_trades(self, db: Session, user_id: int) -> list[Trade]:
        stmt = (
            select(Trade)
            .join(Portfolio, Portfolio.id == Trade.portfolio_id)
            .where(Portfolio.user_id == user_id)
            .order_by(Trade.created_at.desc())
        )
        return list(db.scalars(stmt).all())


trade_service = TradeService()
