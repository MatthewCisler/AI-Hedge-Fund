"""Trade proposal, validation, queueing, and paper execution."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order, QueuedTrade, Trade
from app.models.ai_decision import AIDecision
from app.models.portfolio import Portfolio, Position
from app.schemas.trade import OrderCreate
from app.services.broker_service import broker_service
from app.services.market_schedule import market_schedule_service
from app.services.rules_engine import rules_engine_service


class TradeService:
    def create_order(self, db: Session, user_id: int, payload: OrderCreate, *, execute: bool = True) -> Order | QueuedTrade | dict:
        portfolio = db.scalar(
            select(Portfolio).where(Portfolio.id == payload.portfolio_id, Portfolio.user_id == user_id)
        )
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio not found.")
        decision = self._get_linked_decision(db, user_id, payload)
        if not portfolio.is_active:
            raise ValueError("Portfolio is paused. Resume it before placing an order.")

        ticker = payload.ticker.upper().strip()
        if portfolio.rules.allowed_tickers and ticker not in portfolio.rules.allowed_tickers:
            raise ValueError("Ticker is not in this portfolio's allowed ticker list.")
        if ticker in portfolio.rules.blocked_tickers:
            raise ValueError("Ticker is blocked by this portfolio's rules.")
        position = db.scalar(select(Position).where(Position.portfolio_id == portfolio.id, Position.ticker == ticker))
        pending_sell_quantity = float(db.scalar(
            select(func.coalesce(func.sum(Order.quantity), 0)).where(
                Order.portfolio_id == portfolio.id,
                Order.ticker == ticker,
                Order.side == "sell",
                Order.status == "submitted",
            )
        ) or 0)
        if payload.side == "sell" and (
            not position or float(position.quantity) - pending_sell_quantity < payload.quantity
        ):
            raise ValueError("Sell quantity exceeds the available paper position.")
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
        pending_ticker_buy_value = float(db.scalar(
            select(func.coalesce(func.sum(Order.quantity * Order.requested_price), 0)).where(
                Order.portfolio_id == portfolio.id,
                Order.ticker == ticker,
                Order.side == "buy",
                Order.status == "submitted",
            )
        ) or 0)
        pending_buy_value = float(db.scalar(
            select(func.coalesce(func.sum(Order.quantity * Order.requested_price), 0)).where(
                Order.portfolio_id == portfolio.id,
                Order.side == "buy",
                Order.status == "submitted",
            )
        ) or 0)
        validation = rules_engine_service.validate_trade_idea(
            portfolio=portfolio,
            rules=portfolio.rules,
            ticker=ticker,
            side=payload.side,
            quantity=payload.quantity,
            estimated_price=price,
            average_volume=average_volume,
            asset_type=asset_type or "stock",
            existing_position_value=(position.market_value if position else 0) + pending_ticker_buy_value,
            daily_trade_count=int(daily_trade_count or 0),
            recent_trade_exists=recent_trade_exists,
        )

        if payload.side == "buy":
            required_reserve = float(portfolio.current_value) * (portfolio.rules.cash_reserve_pct / 100)
            if float(portfolio.cash_balance) - pending_buy_value - (price * payload.quantity) < required_reserve:
                validation.approved = False
                validation.reasons.append("Cash reserve rule would be breached.")

        if position and position.sector:
            sector_value = sum(float(item.market_value) for item in portfolio.positions if item.sector == position.sector)
            projected_sector_value = sector_value + (price * payload.quantity if payload.side == "buy" else -(price * payload.quantity))
            if projected_sector_value / float(portfolio.current_value or portfolio.initial_investment) * 100 > portfolio.rules.sector_concentration_limit:
                validation.approved = False
                validation.reasons.append("Sector concentration limit would be exceeded.")

        if not validation.approved:
            if decision:
                decision.rules_result = {"status": "rejected", "approved": False, "reasons": validation.reasons}
                db.commit()
            raise ValueError("; ".join(validation.reasons))

        preview = {
            "approved": True,
            "status": "approved",
            "reasons": validation.reasons or ["All deterministic rules passed."],
            "portfolio_id": portfolio.id,
            "ticker": ticker,
            "side": payload.side,
            "quantity": payload.quantity,
            "estimated_price": price,
            "estimated_dollar_amount": price * payload.quantity,
            "portfolio_cash": float(portfolio.cash_balance),
            "resulting_position_pct": (((float(position.market_value) if position else 0) + (price * payload.quantity if payload.side == "buy" else -(price * payload.quantity))) / float(portfolio.current_value or portfolio.initial_investment) * 100),
            "queue_for_next_open": validation.queue_for_next_open,
            "ai_decision_id": decision.id if decision else None,
            "ai_confidence": decision.confidence_score if decision else None,
            "ai_reasoning": decision.explanation if decision else None,
        }
        if decision:
            decision.rules_result = {"status": "approved", "approved": True, "reasons": preview["reasons"], "preview": {key: preview[key] for key in ("estimated_price", "estimated_dollar_amount", "resulting_position_pct")}}
            db.commit()
        if not execute:
            return preview

        if validation.queue_for_next_open and validation.approved:
            queued = QueuedTrade(
                portfolio_id=portfolio.id,
                ticker=ticker,
                side=payload.side,
                quantity=payload.quantity,
                reason="; ".join(validation.reasons),
                execute_on_market_open=True,
                ai_decision_id=decision.id if decision else None,
            )
            db.add(queued)
            db.commit()
            db.refresh(queued)
            return queued

        order = Order(
            portfolio_id=portfolio.id,
            ticker=ticker,
            side=payload.side,
            quantity=payload.quantity,
            order_type="market",
            status="submitted",
            requested_price=price,
            ai_decision_id=decision.id if decision else None,
            submitted_at=datetime.now(timezone.utc),
            submitted_payload={
                **payload.model_dump(),
                "asset_name": asset_name,
                "asset_type": asset_type,
            },
        )
        db.add(order)
        db.flush()

        broker_result = broker_service.submit_market_order(
            ticker=ticker, side=payload.side, quantity=payload.quantity
        )
        order.status = broker_result.status
        order.broker_order_id = broker_result.broker_order_id
        order.rejection_reason = None if broker_result.status != "rejected" else broker_result.message

        order.submitted_payload = {
            **(order.submitted_payload or {}),
            "broker_status": broker_result.raw_status,
            "simulated": broker_result.simulated,
        }
        if broker_result.status == "filled":
            fill_price = broker_result.filled_average_price or price
            fill_quantity = broker_result.filled_quantity or payload.quantity
            self._record_fill(
                db, order, portfolio, position, fill_quantity, fill_price, asset_name, asset_type,
                "Local simulated paper fill." if broker_result.simulated else "Confirmed Alpaca paper fill.",
            )

        db.commit()
        db.refresh(order)
        return order

    def synchronize_orders(self, db: Session, user_id: int | None = None) -> dict[str, int]:
        stmt = select(Order).join(Portfolio, Portfolio.id == Order.portfolio_id).where(
            Order.status == "submitted", Order.broker_order_id.is_not(None)
        )
        if user_id is not None:
            stmt = stmt.where(Portfolio.user_id == user_id)
        orders = list(db.scalars(stmt).all())
        result = {"checked": 0, "filled": 0, "canceled": 0, "rejected": 0, "pending": 0, "errors": 0}
        for order in orders:
            result["checked"] += 1
            broker_result = broker_service.get_order(order.broker_order_id or "")
            if broker_result.status == "unavailable":
                result["errors"] += 1
                continue
            payload = order.submitted_payload or {}
            order.submitted_payload = {
                **payload,
                "broker_status": broker_result.raw_status,
                "filled_quantity": broker_result.filled_quantity,
                "filled_average_price": broker_result.filled_average_price,
            }
            if broker_result.status == "filled":
                existing_trade = db.scalar(select(Trade).where(Trade.order_id == order.id))
                if existing_trade:
                    order.status = "filled"
                    result["filled"] += 1
                    continue
                if broker_result.filled_quantity <= 0 or not broker_result.filled_average_price:
                    result["errors"] += 1
                    continue
                portfolio = db.get(Portfolio, order.portfolio_id)
                if not portfolio:
                    result["errors"] += 1
                    continue
                position = db.scalar(select(Position).where(Position.portfolio_id == order.portfolio_id, Position.ticker == order.ticker))
                self._record_fill(
                    db, order, portfolio, position, broker_result.filled_quantity,
                    broker_result.filled_average_price, payload.get("asset_name"), payload.get("asset_type"),
                    "Confirmed Alpaca paper fill synchronized from broker.",
                )
                result["filled"] += 1
            elif broker_result.status in {"canceled", "rejected"}:
                order.status = broker_result.status
                order.rejection_reason = broker_result.message if broker_result.status == "rejected" else None
                result[broker_result.status] += 1
            else:
                result["pending"] += 1
        db.commit()
        return result

    def _record_fill(
        self, db: Session, order: Order, portfolio: Portfolio, position: Position | None,
        quantity: float, fill_price: float, asset_name: str | None, asset_type: str | None, notes: str,
    ) -> None:
        order.status = "filled"
        order.filled_at = datetime.now(timezone.utc)
        db.add(Trade(
            order_id=order.id, portfolio_id=portfolio.id, ticker=order.ticker, side=order.side,
            quantity=quantity, fill_price=fill_price, notes=notes,
        ))
        self._apply_fill(db, portfolio, position, order.ticker, order.side, quantity, fill_price, asset_name, asset_type)

    def _get_linked_decision(self, db: Session, user_id: int, payload: OrderCreate) -> AIDecision | None:
        if payload.ai_decision_id is None:
            return None
        decision = db.scalar(
            select(AIDecision).join(Portfolio, Portfolio.id == AIDecision.portfolio_id).where(
                AIDecision.id == payload.ai_decision_id,
                AIDecision.portfolio_id == payload.portfolio_id,
                Portfolio.user_id == user_id,
            )
        )
        if not decision:
            raise ValueError("AI decision not found for this portfolio.")
        if decision.provider != "ollama" or decision.analysis_status != "completed":
            raise ValueError("Only completed Ollama recommendations can be executed.")
        if decision.action_suggestion not in {"buy", "sell"}:
            raise ValueError("This AI decision is not an executable buy or sell recommendation.")
        if decision.ticker != payload.ticker.upper().strip() or decision.action_suggestion != payload.side:
            raise ValueError("Order must match the linked AI recommendation.")
        return decision

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
