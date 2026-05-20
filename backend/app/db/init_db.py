"""Database initialization and local demo seed data."""

from datetime import datetime, timezone

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine
from app.models.ai_decision import AIDecision
from app.models.news_article import NewsArticle
from app.models.portfolio import Portfolio, PortfolioRule, Position
from app.models.user import User
from app.services.benchmark_service import benchmark_service
from app.services.defaults import RISK_PROFILE_DEFAULTS


DEMO_USER_ID = 1


def create_database_schema() -> None:
    """Create all mapped tables for the current SQLAlchemy model set."""
    Base.metadata.create_all(bind=engine)
    _ensure_incremental_columns()


def _ensure_incremental_columns() -> None:
    """Keep local SQLite demo databases compatible as the scaffold grows."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "portfolios" not in table_names or "portfolio_rules" not in table_names:
        return

    portfolio_columns = {column["name"] for column in inspector.get_columns("portfolios")}
    rule_columns = {column["name"] for column in inspector.get_columns("portfolio_rules")}
    statements: list[str] = []
    if "benchmark_symbol" not in portfolio_columns:
        statements.append("ALTER TABLE portfolios ADD COLUMN benchmark_symbol VARCHAR(20) DEFAULT 'SPY'")

    rule_additions = {
        "max_weekly_trades": "INTEGER DEFAULT 15",
        "cash_reserve_pct": "FLOAT DEFAULT 5.0",
        "allowed_tickers": "JSON DEFAULT '[]'",
        "blocked_tickers": "JSON DEFAULT '[]'",
        "aggressiveness": "FLOAT DEFAULT 50.0",
        "after_hours_news_scanning": "BOOLEAN DEFAULT 1",
    }
    for column_name, definition in rule_additions.items():
        if column_name not in rule_columns:
            statements.append(f"ALTER TABLE portfolio_rules ADD COLUMN {column_name} {definition}")

    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def seed_demo_data(db: Session) -> None:
    """Seed enough local data for the X-User-Id: 1 demo flow to work."""
    user = db.get(User, DEMO_USER_ID)
    if not user:
        user = User(
            id=DEMO_USER_ID,
            email="demo@example.com",
            password_hash="local-demo-auth-stub",
            full_name="Demo User",
        )
        db.add(user)
        db.flush()

    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id).limit(1))
    if not portfolio:
        portfolio = Portfolio(
            user_id=user.id,
            name="Demo Paper Portfolio",
            initial_investment=100000,
            cash_balance=86500,
            current_value=100800,
            risk_profile="balanced",
            benchmark_symbol="SPY",
        )
        db.add(portfolio)
        db.flush()
        db.add(PortfolioRule(portfolio_id=portfolio.id, **RISK_PROFILE_DEFAULTS["balanced"]))
        db.add_all(
            [
                Position(
                    portfolio_id=portfolio.id,
                    ticker="SPY",
                    asset_name="SPDR S&P 500 ETF Trust",
                    asset_type="etf",
                    quantity=10,
                    average_cost=450,
                    market_price=455,
                    market_value=4550,
                    unrealized_pnl=50,
                    sector="Broad Market",
                ),
                Position(
                    portfolio_id=portfolio.id,
                    ticker="MSFT",
                    asset_name="Microsoft Corporation",
                    asset_type="stock",
                    quantity=20,
                    average_cost=435,
                    market_price=440,
                    market_value=8800,
                    unrealized_pnl=100,
                    sector="Technology",
                ),
            ]
        )

    if not db.scalar(select(NewsArticle).limit(1)):
        now = datetime.now(timezone.utc)
        db.add_all(
            [
                NewsArticle(
                    source="Local Demo Feed",
                    headline="Broad market ETFs edge higher as technology shares stabilize",
                    url="local-demo://market-etfs",
                    published_at=now,
                    summary="Seed article used when public RSS feeds or network access are unavailable.",
                    inferred_tickers=["SPY", "QQQ", "MSFT"],
                    raw_payload={"provider": "local-demo"},
                ),
                NewsArticle(
                    source="Local Demo Feed",
                    headline="Investors compare cash discipline with AI-generated trade ideas",
                    url="local-demo://paper-trading-risk",
                    published_at=now,
                    summary="Seed article for local AI analysis and report generation.",
                    inferred_tickers=["SPY"],
                    raw_payload={"provider": "local-demo"},
                ),
            ]
        )

    db.commit()

    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id).limit(1))
    if portfolio:
        if not db.scalar(select(AIDecision).where(AIDecision.portfolio_id == portfolio.id).limit(1)):
            db.add(
                AIDecision(
                    portfolio_id=portfolio.id,
                    ticker="SPY",
                    action_suggestion="hold",
                    confidence_score=0.5,
                    explanation="Seed advisory decision for local smoke testing.",
                    input_snapshot={"sentiment_score": 0, "news_urls": ["local-demo://market-etfs"]},
                    rules_result={"status": "advisory_only"},
                )
            )
            db.commit()
        benchmark_service.refresh_for_portfolio(db, portfolio)


def initialize_database(db: Session, *, seed: bool = True) -> None:
    create_database_schema()
    if seed:
        seed_demo_data(db)
