"""Ollama contract, fallback, deduplication, and advisory-only tests."""

import json
import unittest
from unittest.mock import patch

import httpx
from sqlalchemy import func, select

from app.db.init_db import create_database_schema, seed_demo_data
from app.db.session import SessionLocal
from app.models.ai_decision import AIDecision
from app.models.order import Order
from app.services.ai_decision_service import ai_decision_service
from app.services.ai_service import AIAnalysisResult, AISuggestion, OllamaAIService


def response(status: int, payload: dict) -> httpx.Response:
    return httpx.Response(
        status, json=payload, request=httpx.Request("POST", "http://ollama.test/api/chat")
    )


class OllamaAIServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = OllamaAIService("qwen3:8b", "http://ollama.test", timeout_seconds=3)
        self.context = {
            "portfolio_state": {"cash_balance": 9000, "current_value": 10000, "holdings": []},
            "candidate_universe": ["SPY", "MSFT"],
            "recent_news": [{"url": "https://example.com/news", "tickers": ["SPY"]}],
            "price_context": {},
        }

    def valid_envelope(self) -> dict:
        content = {
            "suggestions": [{
                "ticker": "SPY", "action_suggestion": "buy", "confidence_score": 0.72,
                "sentiment_score": 0.2, "quantity": 1,
                "explanation": "Broad-market evidence supports a small advisory paper position.",
                "news_urls": ["https://example.com/news"],
            }]
        }
        return {"message": {"content": f"```json\n{json.dumps(content)}\n```"}}

    @patch("app.services.ai_service.httpx.post")
    def test_successful_valid_ollama_response(self, post) -> None:
        post.return_value = response(200, self.valid_envelope())
        result = self.service.analyze(**self.context)
        self.assertEqual(result.provider, "ollama")
        self.assertEqual(result.analysis_status, "completed")
        self.assertEqual(result.model_name, "qwen3:8b")
        self.assertEqual(result.suggestions[0].ticker, "SPY")
        request_payload = post.call_args.kwargs["json"]
        self.assertIsInstance(request_payload["format"], dict)
        self.assertIn("properties", request_payload["format"])

    @patch("app.services.ai_service.httpx.post")
    def test_ollama_unreachable(self, post) -> None:
        post.side_effect = httpx.ConnectError("refused", request=httpx.Request("POST", "http://ollama.test"))
        result = self.service.analyze(**self.context)
        self.assertEqual((result.provider, result.failure_category), ("deterministic_fallback", "unavailable"))
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0].action_suggestion, "hold")
        self.assertEqual(result.suggestions[0].confidence_score, 0)

    @patch("app.services.ai_service.httpx.post")
    def test_missing_model_response(self, post) -> None:
        post.return_value = response(404, {"error": "model 'qwen3:8b' not found"})
        result = self.service.analyze(**self.context)
        self.assertEqual(result.failure_category, "missing_model")

    @patch("app.services.ai_service.httpx.post")
    def test_timeout(self, post) -> None:
        post.side_effect = httpx.ReadTimeout("slow", request=httpx.Request("POST", "http://ollama.test"))
        result = self.service.analyze(**self.context)
        self.assertEqual(result.failure_category, "timeout")

    @patch("app.services.ai_service.httpx.post")
    def test_malformed_json(self, post) -> None:
        post.return_value = response(200, {"message": {"content": "not JSON at all"}})
        result = self.service.analyze(**self.context)
        self.assertEqual(result.failure_category, "invalid_response")

    @patch("app.services.ai_service.httpx.post")
    def test_valid_json_with_invalid_fields(self, post) -> None:
        invalid = {"suggestions": [{
            "ticker": "NOT ALLOWED!", "action_suggestion": "purchase", "confidence_score": 4,
            "sentiment_score": -8, "quantity": -1, "explanation": "bad", "news_urls": ["secret"],
        }]}
        post.return_value = response(200, {"message": {"content": json.dumps(invalid)}})
        result = self.service.analyze(**self.context)
        self.assertEqual(result.failure_category, "schema_validation")


class AIDecisionPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        create_database_schema()
        with SessionLocal() as db:
            seed_demo_data(db)

    def test_duplicate_fallback_suppression_and_no_trade_execution(self) -> None:
        fallback = AIAnalysisResult(
            suggestions=[AISuggestion(
                ticker="SPY", action_suggestion="hold", confidence_score=0,
                explanation="Deterministic test fallback with insufficient evidence for any action.",
            )],
            provider="deterministic_fallback", analysis_status="fallback",
            failure_category="unavailable", operational_message="Ollama unavailable.",
        )
        with SessionLocal() as db:
            orders_before = db.scalar(select(func.count(Order.id))) or 0
            with (
                patch("app.services.ai_decision_service.ai_service.analyze", return_value=fallback),
                patch("app.services.ai_decision_service.news_service.ingest_latest", return_value=[]),
            ):
                first = ai_decision_service.run_analysis(db, 1)
                second = ai_decision_service.run_analysis(db, 1)
            matching = db.scalar(select(func.count(AIDecision.id)).where(
                AIDecision.portfolio_id == 1,
                AIDecision.provider == "deterministic_fallback",
                AIDecision.explanation == fallback.suggestions[0].explanation,
            ))
            self.assertEqual(matching, 1)
            self.assertEqual(first[0].id, second[0].id)
            self.assertEqual(db.scalar(select(func.count(Order.id))) or 0, orders_before)
            self.assertEqual(first[0].rules_result["status"], "non_actionable_fallback")

    def test_ollama_persistence_is_advisory_and_user_isolated(self) -> None:
        analysis = AIAnalysisResult(
            suggestions=[AISuggestion(
                ticker="MSFT", action_suggestion="buy", confidence_score=0.8, quantity=1,
                explanation="Validated model test result that still requires explicit user confirmation.",
            )],
            provider="ollama", analysis_status="completed", model_name="qwen3:8b",
        )
        with SessionLocal() as db:
            orders_before = db.scalar(select(func.count(Order.id))) or 0
            with (
                patch("app.services.ai_decision_service.ai_service.analyze", return_value=analysis),
                patch("app.services.ai_decision_service.news_service.ingest_latest", return_value=[]),
            ):
                decisions = ai_decision_service.run_analysis(db, 1)
            self.assertEqual(db.scalar(select(func.count(Order.id))) or 0, orders_before)
            self.assertEqual(decisions[0].provider, "ollama")
            other_user_decisions = ai_decision_service.list_for_user(db, 2)
            self.assertFalse(any(item.id == decisions[0].id for item in other_user_decisions))
