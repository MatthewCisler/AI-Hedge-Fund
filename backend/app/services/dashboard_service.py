"""Dashboard aggregation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_decision import AIDecision
from app.models.daily_report import DailyReport
from app.models.news_article import NewsArticle
from app.models.order import Order, QueuedTrade
from app.schemas.dashboard import DashboardResponse
from app.services.portfolio_service import portfolio_service


class DashboardService:
    def build(self, db: Session, user_id: int) -> DashboardResponse:
        portfolios = portfolio_service.list_for_user(db, user_id)
        queued = list(
            db.scalars(
                select(QueuedTrade)
                .join_from(QueuedTrade, QueuedTrade.portfolio)
                .where(QueuedTrade.portfolio.has(user_id=user_id))
                .order_by(QueuedTrade.created_at.desc())
                .limit(10)
            ).all()
        )
        orders = list(
            db.scalars(
                select(Order)
                .join_from(Order, Order.portfolio)
                .where(Order.portfolio.has(user_id=user_id))
                .order_by(Order.created_at.desc())
                .limit(10)
            ).all()
        )
        news = list(db.scalars(select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(10)).all())
        decisions = list(
            db.scalars(
                select(AIDecision)
                .join_from(AIDecision, AIDecision.portfolio)
                .where(AIDecision.portfolio.has(user_id=user_id))
                .order_by(AIDecision.created_at.desc())
                .limit(10)
            ).all()
        )
        reports = list(
            db.scalars(
                select(DailyReport)
                .join_from(DailyReport, DailyReport.portfolio)
                .where(DailyReport.portfolio.has(user_id=user_id))
                .order_by(DailyReport.report_date.desc())
                .limit(10)
            ).all()
        )
        return DashboardResponse(
            portfolios=portfolios,
            queued_trades=queued,
            recent_orders=orders,
            recent_news=news,
            recent_ai_decisions=decisions,
            latest_reports=reports,
        )


dashboard_service = DashboardService()
