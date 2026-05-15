"""News ingestion endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.dashboard import NewsArticleResponse
from app.services.news_service import news_service

router = APIRouter()


@router.get("", response_model=list[NewsArticleResponse])
def ingest_news(
    tickers: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> list[NewsArticleResponse]:
    return news_service.ingest_latest(db, tickers)
