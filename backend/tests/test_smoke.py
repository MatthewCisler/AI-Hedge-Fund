"""Minimal backend route and core service tests."""

import unittest

import httpx

from app.db.init_db import create_database_schema, seed_demo_data
from app.db.session import SessionLocal
from app.main import app
from app.services.broker_service import AlpacaPaperBrokerService, BrokerOrderResult
from app.services.rules_engine import rules_engine_service


class BackendSmokeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        create_database_schema()
        with SessionLocal() as db:
            seed_demo_data(db)

    async def asyncSetUp(self) -> None:
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")
        self.headers = {"X-User-Id": "1"}

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
        self.assertEqual(result.status, "submitted")
        self.assertTrue(result.broker_order_id.startswith("simulated-paper-"))
