"""Local AI model abstraction."""

from dataclasses import dataclass


@dataclass
class AISuggestion:
    ticker: str
    action_suggestion: str
    confidence_score: float
    explanation: str


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
                    explanation=(
                        "Stub local model result. Replace with a real local inference adapter "
                        "for ranking, scoring, and explanation generation."
                    ),
                )
            )
        return suggestions


ai_service: BaseAIService = StubLocalAIService()
