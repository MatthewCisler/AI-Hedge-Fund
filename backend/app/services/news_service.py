"""News ingestion abstraction."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    source: str
    headline: str
    url: str
    published_at: datetime
    summary: str | None = None
    inferred_tickers: list[str] | None = None


class BaseNewsService:
    def fetch_latest(self, tickers: list[str] | None = None) -> list[NewsItem]:
        raise NotImplementedError


class StubNewsService(BaseNewsService):
    def fetch_latest(self, tickers: list[str] | None = None) -> list[NewsItem]:
        logger.info("Using stub news service for tickers=%s", tickers)
        return [
            NewsItem(
                source="Stub RSS",
                headline="Markets closed mixed as investors weighed macro headlines",
                url="https://example.com/stub-market-headline",
                published_at=datetime.now(timezone.utc),
                summary="Placeholder article for development. Replace with RSS/Yahoo-compatible provider.",
                inferred_tickers=tickers or ["SPY"],
            )
        ]


news_service: BaseNewsService = StubNewsService()
