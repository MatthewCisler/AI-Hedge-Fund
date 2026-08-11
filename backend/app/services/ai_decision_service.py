"""AI analysis orchestration, advisory persistence, and fallback deduplication."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.ai_decision import AIDecision
from app.models.news_article import NewsArticle
from app.models.portfolio import Portfolio
from app.services.ai_service import ai_service
from app.services.news_service import news_service

DEFAULT_UNIVERSE = ["SPY", "QQQ", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "VTI"]


class AIDecisionService:
    def run_analysis(self, db: Session, portfolio_id: int) -> list[AIDecision]:
        portfolio = db.scalar(
            select(Portfolio).where(Portfolio.id == portfolio_id).options(
                selectinload(Portfolio.positions), selectinload(Portfolio.rules)
            )
        )
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio not found.")

        candidate_universe = sorted({position.ticker for position in portfolio.positions} | set(DEFAULT_UNIVERSE))
        news_service.ingest_latest(db, candidate_universe)
        articles = list(db.scalars(select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(20)).all())
        news_payload = [{
            "headline": article.headline, "source": article.source, "url": article.url,
            "published_at": article.published_at, "summary": article.summary,
            "tickers": article.inferred_tickers,
        } for article in articles]
        portfolio_state = {
            "id": portfolio.id,
            "name": portfolio.name,
            "risk_profile": portfolio.risk_profile,
            "initial_investment": float(portfolio.initial_investment),
            "current_value": float(portfolio.current_value),
            "cash_balance": float(portfolio.cash_balance),
            "holdings": [{
                "ticker": position.ticker, "quantity": position.quantity,
                "market_value": position.market_value, "unrealized_pnl": position.unrealized_pnl,
            } for position in portfolio.positions],
            "rules": {
                "max_position_size_pct": portfolio.rules.max_position_size_pct,
                "max_daily_trades": portfolio.rules.max_daily_trades,
                "cash_reserve_pct": portfolio.rules.cash_reserve_pct,
                "allowed_tickers": portfolio.rules.allowed_tickers,
                "blocked_tickers": portfolio.rules.blocked_tickers,
                "cooldown_minutes_per_ticker": portfolio.rules.cooldown_minutes_per_ticker,
            },
        }
        result = ai_service.analyze(
            portfolio_state=portfolio_state,
            candidate_universe=candidate_universe,
            recent_news=news_payload,
            price_context={"source": "alpaca-paper-adapter-or-local-fallback"},
        )
        analysis_run_id = str(uuid4())
        decisions: list[AIDecision] = []
        seen: set[tuple[str, str, str]] = set()
        for suggestion in result.suggestions:
            fingerprint = (suggestion.ticker, suggestion.action_suggestion, suggestion.explanation)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            if result.provider == "deterministic_fallback":
                existing = db.scalar(
                    select(AIDecision).where(
                        AIDecision.portfolio_id == portfolio.id,
                        AIDecision.provider == "deterministic_fallback",
                        AIDecision.ticker == suggestion.ticker,
                        AIDecision.action_suggestion == suggestion.action_suggestion,
                        AIDecision.explanation == suggestion.explanation,
                    ).order_by(AIDecision.created_at.desc()).limit(1)
                )
                if existing:
                    decisions.append(existing)
                    continue
            decision = AIDecision(
                portfolio_id=portfolio.id,
                ticker=suggestion.ticker,
                action_suggestion=suggestion.action_suggestion,
                confidence_score=suggestion.confidence_score,
                explanation=suggestion.explanation,
                provider=result.provider,
                model_name=result.model_name,
                analysis_status=result.analysis_status,
                failure_category=result.failure_category,
                analysis_run_id=analysis_run_id,
                input_snapshot={
                    "sentiment_score": suggestion.sentiment_score,
                    "quantity": suggestion.quantity,
                    "news_urls": suggestion.news_urls,
                    "portfolio_state": portfolio_state,
                    "operational_message": result.operational_message,
                },
                rules_result={
                    "status": "pending_user_confirmation" if result.provider == "ollama" else "non_actionable_fallback",
                    "approved": None,
                    "reasons": [
                        "AI and fallback analysis cannot execute trades directly.",
                        "Deterministic rules are evaluated only after explicit user submission.",
                    ],
                },
            )
            db.add(decision)
            decisions.append(decision)
        db.commit()
        for decision in decisions:
            db.refresh(decision)
        return decisions

    def list_for_user(self, db: Session, user_id: int) -> list[AIDecision]:
        rows = list(db.scalars(
            select(AIDecision).join(Portfolio, Portfolio.id == AIDecision.portfolio_id)
            .where(Portfolio.user_id == user_id)
            .order_by(AIDecision.created_at.desc())
            .limit(settings.ai_decision_history_limit * 2)
        ).all())
        history: list[AIDecision] = []
        fallback_seen: set[tuple[int, str, str, str]] = set()
        for decision in rows:
            if decision.provider == "deterministic_fallback":
                key = (decision.portfolio_id, decision.ticker, decision.action_suggestion, decision.explanation)
                if key in fallback_seen:
                    continue
                fallback_seen.add(key)
            history.append(decision)
            if len(history) >= settings.ai_decision_history_limit:
                break
        return history


ai_decision_service = AIDecisionService()
