"""Validated Ollama analysis with explicit, non-actioning fallback metadata."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

import httpx
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.core.config import settings

logger = logging.getLogger(__name__)

FailureCategory = Literal[
    "unavailable", "missing_model", "timeout", "http_error", "empty_response",
    "invalid_response", "schema_validation",
]


class SuggestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,15}$")
    action_suggestion: Literal["buy", "sell", "hold", "rebalance"]
    confidence_score: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)
    quantity: float | None = Field(default=None, ge=0)
    explanation: str = Field(min_length=10, max_length=2000)
    news_urls: list[AnyHttpUrl] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def require_quantity_for_orders(self) -> "SuggestionPayload":
        if self.action_suggestion in {"buy", "sell"} and (self.quantity is None or self.quantity <= 0):
            raise ValueError("buy and sell suggestions require a positive quantity")
        return self


class OllamaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suggestions: list[SuggestionPayload] = Field(default_factory=list, max_length=5)


def ollama_response_schema() -> dict:
    """Use a grammar-friendly schema; Pydantic performs the stricter second validation pass."""
    return {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "action_suggestion": {"type": "string", "enum": ["buy", "sell", "hold", "rebalance"]},
                        "confidence_score": {"type": "number"},
                        "sentiment_score": {"type": "number"},
                        "quantity": {"type": "number"},
                        "explanation": {"type": "string"},
                        "news_urls": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["ticker", "action_suggestion", "confidence_score", "sentiment_score", "quantity", "explanation", "news_urls"],
                },
            }
        },
        "required": ["suggestions"],
    }


@dataclass(frozen=True)
class AISuggestion:
    ticker: str
    action_suggestion: str
    confidence_score: float
    explanation: str
    sentiment_score: float = 0
    quantity: float | None = None
    news_urls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AIAnalysisResult:
    suggestions: list[AISuggestion]
    provider: Literal["ollama", "deterministic_fallback"]
    analysis_status: Literal["completed", "fallback", "failed"]
    model_name: str | None = None
    failure_category: FailureCategory | None = None
    operational_message: str | None = None


class BaseAIService:
    """AI can rank and explain ideas, but cannot execute trades."""

    def analyze(self, portfolio_state: dict, candidate_universe: list[str], recent_news: list[dict], price_context: dict) -> AIAnalysisResult:
        raise NotImplementedError

    def status(self) -> dict:
        return {"status": "offline", "provider": "deterministic_fallback", "model_name": None, "failure_category": "unavailable"}


class DeterministicFallbackAIService(BaseAIService):
    """Return at most one non-actionable, portfolio-aware hold observation."""

    def analyze(
        self, portfolio_state: dict, candidate_universe: list[str], recent_news: list[dict],
        price_context: dict, *, failure_category: FailureCategory = "unavailable",
    ) -> AIAnalysisResult:
        holdings = list(portfolio_state.get("holdings") or [])
        cash = float(portfolio_state.get("cash_balance") or 0)
        value = float(portfolio_state.get("current_value") or portfolio_state.get("initial_investment") or 0)
        cash_pct = (cash / value * 100) if value > 0 else 100
        news_tickers = {
            str(ticker).upper()
            for article in recent_news
            for ticker in (article.get("tickers") or [])
        }
        if holdings:
            holding = max(holdings, key=lambda item: float(item.get("market_value") or 0))
            ticker = str(holding.get("ticker") or "").upper()
            news_note = "Relevant recent news is available" if ticker in news_tickers else "No ticker-specific recent news was available"
            explanation = (
                f"Deterministic safety fallback: {ticker} is the largest existing holding; {news_note.lower()}, "
                f"and cash is {cash_pct:.1f}% of portfolio value. Hold for review until Ollama analysis is restored."
            )
            suggestions = [AISuggestion(
                ticker=ticker, action_suggestion="hold", confidence_score=0,
                sentiment_score=0, quantity=None, explanation=explanation,
                news_urls=[str(item.get("url")) for item in recent_news if ticker in (item.get("tickers") or []) and item.get("url")][:3],
            )]
        else:
            ticker = next((item for item in candidate_universe if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,15}", item)), "SPY")
            suggestions = [AISuggestion(
                ticker=ticker, action_suggestion="hold", confidence_score=0, sentiment_score=0,
                explanation=(
                    f"Deterministic safety fallback: the portfolio has no holdings and is {cash_pct:.1f}% cash. "
                    "Evidence is insufficient for an actionable recommendation; wait for validated Ollama analysis."
                ),
            )]
        return AIAnalysisResult(
            suggestions=suggestions, provider="deterministic_fallback", analysis_status="fallback",
            failure_category=failure_category,
            operational_message="Ollama analysis is unavailable. Check the configured server and model on the backend host.",
        )

    def status(self) -> dict:
        return {"status": "offline", "provider": "deterministic_fallback", "model_name": None, "failure_category": "unavailable"}


class OllamaAIService(BaseAIService):
    """Ollama adapter using a JSON Schema response format and strict validation."""

    def __init__(self, model: str, base_url: str, timeout_seconds: float = 90) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback = DeterministicFallbackAIService()

    def analyze(self, portfolio_state: dict, candidate_universe: list[str], recent_news: list[dict], price_context: dict) -> AIAnalysisResult:
        prompt = self._build_prompt(portfolio_state, candidate_universe, recent_news, price_context)
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "think": False,
                    "format": ollama_response_schema(),
                    "options": {"temperature": 0},
                    "messages": [
                        {"role": "system", "content": "You are an advisory-only paper-trading research assistant. Return only JSON matching the supplied schema. Never claim to execute a trade."},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code >= 400:
                response_hint = response.text[:500].lower()
                category: FailureCategory = (
                    "missing_model"
                    if response.status_code == 404 or ("model" in response_hint and "not found" in response_hint)
                    else "http_error"
                )
                self._log_failure(category, f"HTTP {response.status_code}")
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, category)
            try:
                envelope = response.json()
            except (json.JSONDecodeError, ValueError) as exc:
                self._log_failure("invalid_response", type(exc).__name__)
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "invalid_response")
            content = envelope.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                self._log_failure("empty_response", "empty message content")
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "empty_response")
            try:
                raw_payload = self._load_json(content)
            except (json.JSONDecodeError, ValueError) as exc:
                self._log_failure("invalid_response", type(exc).__name__)
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "invalid_response")
            try:
                payload = OllamaPayload.model_validate(raw_payload)
            except ValidationError as exc:
                fields = sorted({str(item["loc"][0]) for item in exc.errors() if item.get("loc")})
                self._log_failure("schema_validation", f"invalid fields={','.join(fields) or 'unknown'}")
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "schema_validation")
            allowed_tickers = set(candidate_universe)
            if any(item.ticker not in allowed_tickers for item in payload.suggestions):
                self._log_failure("schema_validation", "suggestion ticker outside candidate universe")
                return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "schema_validation")
            suggestions = [AISuggestion(
                ticker=item.ticker, action_suggestion=item.action_suggestion,
                confidence_score=item.confidence_score, sentiment_score=item.sentiment_score,
                quantity=item.quantity, explanation=item.explanation,
                news_urls=[str(url) for url in item.news_urls],
            ) for item in payload.suggestions]
            logger.info(
                "Ollama analysis completed model=%s suggestions=%s duration_ns=%s",
                self.model, len(suggestions), envelope.get("total_duration"),
            )
            return AIAnalysisResult(
                suggestions=suggestions, provider="ollama", analysis_status="completed", model_name=self.model,
            )
        except httpx.TimeoutException as exc:
            self._log_failure("timeout", type(exc).__name__)
            return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "timeout")
        except httpx.ConnectError as exc:
            self._log_failure("unavailable", type(exc).__name__)
            return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "unavailable")
        except httpx.HTTPError as exc:
            self._log_failure("http_error", type(exc).__name__)
            return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "http_error")
        except Exception as exc:
            self._log_failure("invalid_response", type(exc).__name__)
            return self._fallback(portfolio_state, candidate_universe, recent_news, price_context, "invalid_response")

    def status(self) -> dict:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=min(10, self.timeout_seconds))
            if response.status_code >= 400:
                return {"status": "error", "provider": "ollama", "model_name": self.model, "failure_category": "http_error"}
            models = response.json().get("models", [])
            installed = any(item.get("name") == self.model or item.get("model") == self.model for item in models)
            return {
                "status": "online" if installed else "error",
                "provider": "ollama",
                "model_name": self.model,
                "failure_category": None if installed else "missing_model",
            }
        except httpx.TimeoutException:
            return {"status": "error", "provider": "ollama", "model_name": self.model, "failure_category": "timeout"}
        except httpx.HTTPError:
            return {"status": "offline", "provider": "ollama", "model_name": self.model, "failure_category": "unavailable"}
        except (ValueError, TypeError):
            return {"status": "error", "provider": "ollama", "model_name": self.model, "failure_category": "invalid_response"}

    def _fallback(self, portfolio_state: dict, candidate_universe: list[str], recent_news: list[dict], price_context: dict, category: FailureCategory) -> AIAnalysisResult:
        return self.fallback.analyze(
            portfolio_state, candidate_universe, recent_news, price_context, failure_category=category,
        )

    def _log_failure(self, category: FailureCategory, detail: str) -> None:
        logger.warning(
            "Ollama analysis failed category=%s model=%s url=%s detail=%s",
            category, self.model, self.base_url, detail[:300],
        )

    def _build_prompt(self, portfolio_state: dict, candidate_universe: list[str], recent_news: list[dict], price_context: dict) -> str:
        return json.dumps({
            "task": "Provide zero to five evidence-based advisory paper-trading suggestions. Return no actionable suggestion when evidence is insufficient.",
            "response_schema": ollama_response_schema(),
            "constraints": [
                "Use only tickers in candidate_universe.",
                "Only U.S. stocks and ETFs.",
                "AI cannot execute, queue, or approve trades.",
                "Use a positive estimated quantity for buy/sell and quantity 0 for hold/rebalance.",
                "Cite only news URLs supplied in recent_news.",
            ],
            "portfolio_state": portfolio_state,
            "candidate_universe": candidate_universe,
            "recent_news": recent_news[:20],
            "price_context": price_context,
        }, default=str)

    def _load_json(self, content: str) -> dict:
        cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content.strip(), flags=re.IGNORECASE)
        try:
            payload = json.loads(cleaned)
            if not isinstance(payload, dict):
                raise ValueError("root must be an object")
            return payload
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            for index, character in enumerate(cleaned):
                if character != "{":
                    continue
                try:
                    payload, _ = decoder.raw_decode(cleaned[index:])
                    if isinstance(payload, dict):
                        return payload
                except json.JSONDecodeError:
                    continue
            raise


ai_service: BaseAIService = (
    OllamaAIService(settings.ollama_model, settings.ollama_url, settings.ollama_timeout_seconds)
    if settings.local_ai_provider == "ollama"
    else DeterministicFallbackAIService()
)
