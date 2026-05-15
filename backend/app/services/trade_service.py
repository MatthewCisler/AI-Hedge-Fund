"""Trade proposal, validation, queueing, and paper execution."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order, QueuedTrade, Trade
from app.models.portfolio import Portfolio, Position
from app.schemas.trade import OrderCreate
from app.services.broker_service import broker_service
from app.services.market_schedule import market_schedule_service
from app.services.rules_engine import rules_engine_service


class TradeService:
    def create_order(self, db: Session, user_id: int, payload: OrderCreate) -> Order | QueuedTrade:
        portfolio = db.scalar(
            select(Portfolio).where(Portfolio.id == payload.portfolio_id, Portfolio.user_id == user_id)
        )
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio not found.")

        ticker = payload.ticker.upper().strip()
        position = db.scalar(select(Position).where(Position.portfolio_id == portfolio.id, Position.ticker == ticker))
        asset_valid, asset_name, asset_type = broker_service.asset_is_tradable_us_equity_or_etf(ticker)
        if not asset_valid:
            raise ValueError("Only tradable U.S. stocks and ETFs are allowed.")
        price = broker_service.latest_price(ticker) or (position.market_price if position else 100.0)
        average_volume = broker_service.average_daily_volume(ticker)
        start_of_day = market_schedule_service.now_ct().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_trade_count = db.scalar(
            select(func.count(Trade.id)).where(Trade.portfolio_id == portfolio.id, Trade.created_at >= start_of_day)
        )
        cooldown_cutoff = rules_engine_service.cooldown_cutoff(portfolio.rules.cooldown_minutes_per_ticker)
        recent_trade_exists = (
            db.scalar(
                select(Trade)
                .where(
                    Trade.portfolio_id == portfolio.id,
                    Trade.ticker == ticker,
                    Trade.created_at >= cooldown_cutoff,
                )
                .limit(1)
            )
            is not None
        )
        validation = rules_engine_service.validate_trade_idea(
            portfolio=portfolio,
            rules=portfolio.rules,
            ticker=ticker,
            side=payload.side,
            quantity=payload.quantity,
            estimated_price=price,
            average_volume=average_volume,
            asset_type=asset_type or "stock",
            existing_position_value=position.market_value if position else 0,
            daily_trade_count=int(daily_trade_count or 0),
            recent_trade_exists=recent_trade_exists,
        )

        if validation.queue_for_next_open and validation.approved:
            queued = QueuedTrade(
                portfolio_id=portfolio.id,
                ticker=ticker,
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
            ticker=ticker,
            side=payload.side,
            quantity=payload.quantity,
            order_type="market",
            status="submitted",
            requested_price=price,
            submitted_payload=payload.model_dump(),
        )
        db.add(order)
        db.flush()

        broker_result = broker_service.submit_market_order(
            ticker=ticker, side=payload.side, quantity=payload.quantity
        )
        order.status = broker_result.status
        order.broker_order_id = broker_result.broker_order_id
        order.rejection_reason = None if broker_result.status != "rejected" else broker_result.message

        if broker_result.status == "submitted":
            trade = Trade(
                order_id=order.id,
                portfolio_id=portfolio.id,
                ticker=ticker,
                side=payload.side,
                quantity=payload.quantity,
                fill_price=price,
                notes="Paper trade execution through Alpaca paper adapter.",
            )
            db.add(trade)
            self._apply_fill(db, portfolio, position, ticker, payload.side, payload.quantity, price, asset_name, asset_type)

        db.commit()
        db.refresh(order)
        return order

    def _apply_fill(
        self,
        db: Session,
        portfolio: Portfolio,
        position: Position | None,
        ticker: str,
        side: str,
        quantity: float,
        fill_price: float,
        asset_name: str | None,
        asset_type: str | None,
    ) -> None:
        trade_value = quantity * fill_price
        if side == "buy":
            portfolio.cash_balance = float(portfolio.cash_balance) - trade_value
            if not position:
                position = Position(
                    portfolio_id=portfolio.id,
                    ticker=ticker,
                    asset_name=asset_name,
                    asset_type=asset_type or "stock",
                    quantity=0,
                    average_cost=0,
                )
                db.add(position)
                portfolio.positions.append(position)
            new_quantity = float(position.quantity) + quantity
            existing_cost = float(position.average_cost) * float(position.quantity)
            position.average_cost = (existing_cost + trade_value) / new_quantity if new_quantity else 0
            position.quantity = new_quantity
        else:
            if position:
                position.quantity = max(0, float(position.quantity) - quantity)
            portfolio.cash_balance = float(portfolio.cash_balance) + trade_value
        if position:
            position.market_price = fill_price
            position.market_value = float(position.quantity) * fill_price
            position.unrealized_pnl = position.market_value - (float(position.average_cost) * float(position.quantity))
        portfolio.current_value = float(portfolio.cash_balance) + sum(float(pos.market_value) for pos in portfolio.positions)

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
