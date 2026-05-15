"""AI decision orchestration and persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_decision import AIDecision
from app.models.news_article import NewsArticle
from app.models.portfolio import Portfolio
from app.services.ai_service import ai_service
from app.services.news_service import news_service
from app.services.rules_engine import rules_engine_service

DEFAULT_UNIVERSE = ["SPY", "QQQ", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "VTI"]


class AIDecisionService:
    def run_analysis(self, db: Session, portfolio_id: int) -> list[AIDecision]:
        portfolio = db.scalar(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .options(selectinload(Portfolio.positions), selectinload(Portfolio.rules))
        )
        if not portfolio or not portfolio.rules:
            raise ValueError("Portfolio not found.")

        candidate_universe = sorted({position.ticker for position in portfolio.positions} | set(DEFAULT_UNIVERSE))
        news_service.ingest_latest(db, candidate_universe)
        articles = list(
            db.scalars(select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(20)).all()
        )
        news_payload = [
            {
                "headline": article.headline,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at,
                "summary": article.summary,
                "tickers": article.inferred_tickers,
            }
            for article in articles
        ]
        portfolio_state = {
            "id": portfolio.id,
            "name": portfolio.name,
            "risk_profile": portfolio.risk_profile,
            "initial_investment": float(portfolio.initial_investment),
            "current_value": float(portfolio.current_value),
            "cash_balance": float(portfolio.cash_balance),
            "holdings": [
                {
                    "ticker": position.ticker,
                    "quantity": position.quantity,
                    "market_value": position.market_value,
                    "unrealized_pnl": position.unrealized_pnl,
                }
                for position in portfolio.positions
            ],
            "rules": {
                "max_position_size_pct": portfolio.rules.max_position_size_pct,
                "max_daily_trades": portfolio.rules.max_daily_trades,
                "cooldown_minutes_per_ticker": portfolio.rules.cooldown_minutes_per_ticker,
            },
        }
        suggestions = ai_service.analyze(
            portfolio_state=portfolio_state,
            candidate_universe=candidate_universe,
            recent_news=news_payload,
            price_context={"source": "alpaca-paper-adapter-or-local-fallback"},
        )
        decisions: list[AIDecision] = []
        for suggestion in suggestions:
            decision = AIDecision(
                portfolio_id=portfolio.id,
                ticker=suggestion.ticker,
                action_suggestion=suggestion.action_suggestion,
                confidence_score=suggestion.confidence_score,
                explanation=suggestion.explanation,
                input_snapshot={
                    "sentiment_score": suggestion.sentiment_score,
                    "quantity": suggestion.quantity,
                    "news_urls": suggestion.news_urls,
                    "portfolio_state": portfolio_state,
                },
                rules_result={"status": "advisory_only", "reasons": ["AI cannot execute trades directly."]},
            )
            decisions.append(decision)
            db.add(decision)
        db.commit()
        for decision in decisions:
            db.refresh(decision)
        return decisions

    def list_for_user(self, db: Session, user_id: int) -> list[AIDecision]:
        return list(
            db.scalars(
                select(AIDecision)
                .join(Portfolio, Portfolio.id == AIDecision.portfolio_id)
                .where(Portfolio.user_id == user_id)
                .order_by(AIDecision.created_at.desc())
            ).all()
        )


ai_decision_service = AIDecisionService()
