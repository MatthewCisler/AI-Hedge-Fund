"""Top-level API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import ai, auth, dashboard, news, portfolios, reports, settings, trades

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
