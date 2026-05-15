"""Local AI model abstraction."""

import json
import logging
import re
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AISuggestion:
    ticker: str
    action_suggestion: str
    confidence_score: float
    explanation: str
    sentiment_score: float = 0
    quantity: float | None = None
    news_urls: list[str] | None = None


class BaseAIService:
    """AI can rank and explain ideas, but not execute trades."""

    def analyze(
        self,
        portfolio_state: dict,
        candidate_universe: list[str],
        recent_news: list[dict],
        price_context: dict,
    ) -> list[AISuggestion]:
        raise NotImplementedError


class StubLocalAIService(BaseAIService):
    def analyze(
        self,
        portfolio_state: dict,
        candidate_universe: list[str],
        recent_news: list[dict],
        price_context: dict,
    ) -> list[AISuggestion]:
        suggestions: list[AISuggestion] = []
        for ticker in candidate_universe[:5]:
            suggestions.append(
                AISuggestion(
                    ticker=ticker,
                    action_suggestion="hold",
                    confidence_score=0.5,
                    sentiment_score=0,
                    explanation=(
                        "Fallback local result. Ollama was unavailable or returned invalid JSON."
                    ),
                    news_urls=[item.get("url", "") for item in recent_news[:3] if item.get("url")],
                )
            )
        return suggestions


class OllamaAIService(BaseAIService):
    """Ollama-backed adapter. It returns advisory JSON only."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.fallback = StubLocalAIService()

    def analyze(
        self,
        portfolio_state: dict,
        candidate_universe: list[str],
        recent_news: list[dict],
        price_context: dict,
    ) -> list[AISuggestion]:
        prompt = self._build_prompt(portfolio_state, candidate_universe, recent_news, price_context)
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a paper-trading research assistant. "
                                "You cannot execute trades. Return strict JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60,
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            payload = self._load_json(content)
            suggestions = payload.get("suggestions", payload if isinstance(payload, list) else [])
            parsed = [self._parse_suggestion(item) for item in suggestions if isinstance(item, dict)]
            return [item for item in parsed if item]
        except Exception as exc:
            logger.warning("Ollama analysis failed; using fallback suggestions: %s", exc)
            return self.fallback.analyze(portfolio_state, candidate_universe, recent_news, price_context)

    def _build_prompt(
        self,
        portfolio_state: dict,
        candidate_universe: list[str],
        recent_news: list[dict],
        price_context: dict,
    ) -> str:
        return json.dumps(
            {
                "task": (
                    "Summarize public financial news, score sentiment, and suggest buy/sell/hold/"
                    "rebalance ideas for a play-money paper portfolio. Suggestions are advisory only."
                ),
                "required_json_schema": {
                    "suggestions": [
                        {
                            "ticker": "AAPL",
                            "action_suggestion": "buy|sell|hold|rebalance",
                            "confidence_score": 0.0,
                            "sentiment_score": 0.0,
                            "quantity": 1.0,
                            "explanation": "short reason",
                            "news_urls": ["https://..."],
                        }
                    ]
                },
                "constraints": [
                    "Only U.S. stocks and ETFs.",
                    "Do not claim to execute trades.",
                    "Keep confidence_score between 0 and 1.",
                    "Keep sentiment_score between -1 and 1.",
                ],
                "portfolio_state": portfolio_state,
                "candidate_universe": candidate_universe,
                "recent_news": recent_news[:20],
                "price_context": price_context,
            },
            default=str,
        )

    def _load_json(self, content: str) -> dict | list:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(1))

    def _parse_suggestion(self, item: dict) -> AISuggestion | None:
        ticker = str(item.get("ticker", "")).upper().strip()
        action = str(item.get("action_suggestion", "hold")).lower().strip()
        if not ticker or action not in {"buy", "sell", "hold", "rebalance"}:
            return None
        confidence = max(0.0, min(1.0, float(item.get("confidence_score", 0.5))))
        sentiment = max(-1.0, min(1.0, float(item.get("sentiment_score", 0))))
        quantity = item.get("quantity")
        return AISuggestion(
            ticker=ticker,
            action_suggestion=action,
            confidence_score=confidence,
            sentiment_score=sentiment,
            quantity=float(quantity) if quantity is not None else None,
            explanation=str(item.get("explanation", "No explanation provided."))[:2000],
            news_urls=list(item.get("news_urls") or []),
        )


ai_service: BaseAIService = (
    OllamaAIService(settings.ollama_model, settings.ollama_url)
    if settings.local_ai_provider == "ollama"
    else StubLocalAIService()
)
