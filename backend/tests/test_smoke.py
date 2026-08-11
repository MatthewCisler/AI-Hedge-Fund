"""Minimal backend route and core service tests."""

import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx
from sqlalchemy import func, select

from app.core.security import create_access_token
from app.db.init_db import create_database_schema, seed_demo_data
from app.db.session import SessionLocal
from app.main import app
from app.services.broker_service import AlpacaPaperBrokerService, BrokerOrderResult
from app.services.rules_engine import rules_engine_service
from app.services.trade_service import trade_service
from app.schemas.trade import OrderCreate
from app.models.order import Order, QueuedTrade, Trade
from app.models.ai_decision import AIDecision
from app.models.portfolio import Portfolio
from app.models.user import User
from app.core.security import hash_password


class BackendSmokeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        create_database_schema()
        with SessionLocal() as db:
            seed_demo_data(db)

    async def asyncSetUp(self) -> None:
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")
        self.headers = {"Authorization": f"Bearer {create_access_token('1')}"}

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_core_get_routes(self) -> None:
        for path in [
            "/health",
            "/api/v1/dashboard",
            "/api/v1/portfolios",
            "/api/v1/trades/orders",
            "/api/v1/trades/queued",
            "/api/v1/trades",
            "/api/v1/ai/decisions",
            "/api/v1/ai/status",
            "/api/v1/trades/broker/status",
            "/api/v1/settings/system-status",
            "/api/v1/reports",
            "/api/v1/settings/risk-profile-defaults",
        ]:
            with self.subTest(path=path):
                response = await self.client.get(path, headers=self.headers)
                self.assertEqual(response.status_code, 200, response.text)

    async def test_manual_report_and_ai_debug_routes(self) -> None:
        ai_response = await self.client.post("/api/v1/ai/debug-sample", headers=self.headers)
        self.assertEqual(ai_response.status_code, 200, ai_response.text)
        self.assertIn("suggestions", ai_response.json())

        report_response = await self.client.post(
            "/api/v1/reports/generate?portfolio_id=1",
            headers=self.headers,
        )
        self.assertEqual(report_response.status_code, 201, report_response.text)
        self.assertEqual(report_response.json()["portfolio_id"], 1)

    async def test_bearer_auth_is_required_and_client_user_id_is_ignored(self) -> None:
        missing = await self.client.get("/api/v1/portfolios", headers={"X-User-Id": "1"})
        self.assertEqual(missing.status_code, 401)

        invalid = await self.client.get("/api/v1/portfolios", headers={"Authorization": "Bearer invalid"})
        self.assertEqual(invalid.status_code, 401)

    async def test_portfolios_are_strictly_isolated_by_token_subject(self) -> None:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == "isolation@example.com"))
            if not user:
                user = User(email="isolation@example.com", password_hash=hash_password("test-password"))
                db.add(user)
                db.commit()
                db.refresh(user)
            user_id = user.id
        other_headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}
        listing = await self.client.get("/api/v1/portfolios", headers=other_headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json(), [])
        forbidden_lookup = await self.client.get("/api/v1/portfolios/1", headers=other_headers)
        self.assertEqual(forbidden_lookup.status_code, 404)

    async def test_register_login_and_session_flow(self) -> None:
        email = "auth-flow@example.com"
        registration = await self.client.post("/api/v1/auth/register", json={"email": email, "password": "strong-password", "full_name": "Auth Test"})
        if registration.status_code == 400:
            login = await self.client.post("/api/v1/auth/login", json={"email": email, "password": "strong-password"})
        else:
            self.assertEqual(registration.status_code, 200, registration.text)
            login = registration
        token = login.json()["access_token"]
        session = await self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(session.status_code, 200, session.text)
        self.assertEqual(session.json()["email"], email)

    async def test_authenticated_portfolio_to_paper_order_workflow(self) -> None:
        email = "vertical-slice@example.com"
        registration = await self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "strong-password", "full_name": "Workflow Test"},
        )
        if registration.status_code == 400:
            registration = await self.client.post(
                "/api/v1/auth/login", json={"email": email, "password": "strong-password"}
            )
        headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
        portfolios = await self.client.get("/api/v1/portfolios", headers=headers)
        existing = portfolios.json()
        if existing:
            portfolio_id = existing[0]["id"]
        else:
            created = await self.client.post(
                "/api/v1/portfolios",
                headers=headers,
                json={
                    "name": "Vertical Slice Fund",
                    "initial_investment": 100000,
                    "risk_profile": "balanced",
                    "benchmark_symbol": "SPY",
                },
            )
            self.assertEqual(created.status_code, 201, created.text)
            portfolio_id = created.json()["id"]

        rules = await self.client.get(f"/api/v1/portfolios/{portfolio_id}/rules", headers=headers)
        rule_payload = rules.json()
        rule_payload.pop("portfolio_id", None)
        rule_payload.pop("created_at", None)
        rule_payload.pop("updated_at", None)
        rule_payload["blocked_tickers"] = ["GME"]
        rule_payload["cooldown_minutes_per_ticker"] = 0
        updated = await self.client.patch(
            f"/api/v1/portfolios/{portfolio_id}/rules", headers=headers, json=rule_payload
        )
        self.assertEqual(updated.status_code, 200, updated.text)

        rejected = await self.client.post(
            "/api/v1/trades/orders",
            headers=headers,
            json={"portfolio_id": portfolio_id, "ticker": "GME", "side": "buy", "quantity": 1},
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertIn("blocked", rejected.json()["detail"].lower())

        workflow_ticker = f"T{uuid4().hex[:7].upper()}"
        submitted = await self.client.post(
            "/api/v1/trades/orders",
            headers=headers,
            json={"portfolio_id": portfolio_id, "ticker": workflow_ticker, "side": "buy", "quantity": 1},
        )
        self.assertEqual(submitted.status_code, 201, submitted.text)
        activity = await self.client.get("/api/v1/trades", headers=headers)
        self.assertEqual(activity.status_code, 200)

    async def test_ai_decision_preflight_does_not_execute_and_links_confirmed_paper_action(self) -> None:
        ticker = f"A{uuid4().hex[:7].upper()}"
        with SessionLocal() as db:
            decision = AIDecision(
                portfolio_id=1, ticker=ticker, action_suggestion="buy", confidence_score=0.81,
                explanation="Validated Ollama test recommendation requiring explicit execution confirmation.",
                provider="ollama", model_name="qwen3:8b", analysis_status="completed",
                analysis_run_id=str(uuid4()), input_snapshot={"quantity": 1},
                rules_result={"status": "pending_user_confirmation"},
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            decision_id = decision.id
            orders_before = db.scalar(select(func.count(Order.id))) or 0

        payload = {"portfolio_id": 1, "ticker": ticker, "side": "buy", "quantity": 1, "ai_decision_id": decision_id}
        preview = await self.client.post("/api/v1/trades/orders/validate", headers=self.headers, json=payload)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertTrue(preview.json()["approved"])
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count(Order.id))) or 0, orders_before)

        execution = await self.client.post("/api/v1/trades/orders", headers=self.headers, json=payload)
        self.assertEqual(execution.status_code, 201, execution.text)
        with SessionLocal() as db:
            linked_order = db.scalar(select(Order).where(Order.ai_decision_id == decision_id))
            linked_queue = db.scalar(select(QueuedTrade).where(QueuedTrade.ai_decision_id == decision_id))
            self.assertTrue(linked_order is not None or linked_queue is not None)

    def test_rules_engine_blocks_oversized_buy(self) -> None:
        class Portfolio:
            current_value = 1000
            initial_investment = 1000
            cash_balance = 100

        class Rules:
            allow_queued_after_hours = True
            minimum_liquidity_volume = 0
            etf_allowed = True
            max_daily_trades = 10
            max_position_size_pct = 10

        result = rules_engine_service.validate_trade_idea(
            portfolio=Portfolio(),
            rules=Rules(),
            ticker="SPY",
            side="buy",
            quantity=10,
            estimated_price=100,
            average_volume=1_000_000,
        )
        self.assertFalse(result.approved)
        self.assertIn("Max position size exceeded.", result.reasons)

    def test_broker_refuses_live_endpoint(self) -> None:
        broker = AlpacaPaperBrokerService()
        broker.base_url = "https://api.alpaca.markets"
        with self.assertRaises(RuntimeError):
            broker.submit_market_order(ticker="SPY", side="buy", quantity=1)

    def test_unconfigured_broker_uses_mock_paper_order(self) -> None:
        broker = AlpacaPaperBrokerService()
        result = broker.submit_market_order(ticker="SPY", side="buy", quantity=1)
        self.assertIsInstance(result, BrokerOrderResult)
        self.assertEqual(result.status, "filled")
        self.assertTrue(result.simulated)
        self.assertTrue(result.broker_order_id.startswith("simulated-paper-"))

    def test_broker_fill_sync_is_idempotent_and_user_scoped(self) -> None:
        broker_id = f"alpaca-test-{uuid4()}"
        with SessionLocal() as db:
            portfolio = db.get(Portfolio, 1)
            self.assertIsNotNone(portfolio)
            starting_cash = float(portfolio.cash_balance)
            order = Order(
                portfolio_id=1,
                ticker="SYNC",
                side="buy",
                quantity=2,
                order_type="market",
                status="submitted",
                broker_order_id=broker_id,
                requested_price=25,
                submitted_payload={"asset_type": "stock"},
            )
            db.add(order)
            db.commit()
            order_id = order.id

            filled = BrokerOrderResult(
                status="filled",
                broker_order_id=broker_id,
                filled_quantity=2,
                filled_average_price=25,
                raw_status="filled",
            )
            with patch("app.services.trade_service.broker_service.get_order", return_value=filled):
                first = trade_service.synchronize_orders(db, user_id=1)
                second = trade_service.synchronize_orders(db, user_id=1)

            self.assertEqual(first["filled"], 1)
            self.assertEqual(second["checked"], 0)
            self.assertEqual(db.scalar(select(Trade).where(Trade.order_id == order_id)).quantity, 2)
            db.refresh(portfolio)
            self.assertEqual(float(portfolio.cash_balance), starting_cash - 50)

    def test_pending_sell_orders_reserve_position_quantity(self) -> None:
        with SessionLocal() as db:
            pending = Order(
                portfolio_id=1, ticker="SPY", side="sell", quantity=9, order_type="market",
                status="submitted", broker_order_id=f"pending-sell-{uuid4()}", requested_price=100,
            )
            db.add(pending)
            db.commit()
            with self.assertRaisesRegex(ValueError, "available paper position"):
                trade_service.create_order(
                    db, 1, OrderCreate(portfolio_id=1, ticker="SPY", side="sell", quantity=2)
                )
            pending.status = "canceled"
            db.commit()
