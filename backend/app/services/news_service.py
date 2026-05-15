"""News ingestion abstraction."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)
TICKER_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")


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

    def ingest_latest(self, db: Session, tickers: list[str] | None = None) -> list[NewsArticle]:
        raise NotImplementedError


class RssNewsService(BaseNewsService):
    def __init__(self, sources: list[str]) -> None:
        self.sources = sources

    def fetch_latest(self, tickers: list[str] | None = None) -> list[NewsItem]:
        items: list[NewsItem] = []
        for source_url in self.sources:
            try:
                response = httpx.get(source_url, timeout=20, follow_redirects=True)
                response.raise_for_status()
                items.extend(self._parse_feed(source_url, response.text, tickers))
            except Exception as exc:
                logger.warning("RSS source failed %s: %s", source_url, exc)
        return self._dedupe(items)

    def ingest_latest(self, db: Session, tickers: list[str] | None = None) -> list[NewsArticle]:
        articles: list[NewsArticle] = []
        for item in self.fetch_latest(tickers):
            exists = db.scalar(select(NewsArticle).where(NewsArticle.url == item.url))
            if exists:
                continue
            article = NewsArticle(
                source=item.source,
                headline=item.headline,
                url=item.url,
                published_at=item.published_at,
                summary=item.summary,
                inferred_tickers=item.inferred_tickers,
                raw_payload={"provider": "rss"},
            )
            db.add(article)
            articles.append(article)
        db.commit()
        for article in articles:
            db.refresh(article)
        return articles

    def _parse_feed(self, source_url: str, xml_text: str, tickers: list[str] | None) -> list[NewsItem]:
        root = ElementTree.fromstring(xml_text)
        channel_title = root.findtext("./channel/title") or source_url
        items: list[NewsItem] = []
        for node in root.findall(".//item")[:50]:
            headline = (node.findtext("title") or "").strip()
            url = (node.findtext("link") or "").strip()
            if not headline or not url:
                continue
            summary = re.sub("<[^<]+?>", "", node.findtext("description") or "").strip()[:1000] or None
            published_at = self._parse_datetime(node.findtext("pubDate"))
            inferred = self._infer_tickers(f"{headline} {summary or ''}", tickers)
            items.append(
                NewsItem(
                    source=channel_title[:120],
                    headline=headline[:500],
                    url=url,
                    published_at=published_at,
                    summary=summary,
                    inferred_tickers=inferred,
                )
            )
        return items

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            parsed = parsedate_to_datetime(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _infer_tickers(self, text: str, requested: list[str] | None) -> list[str]:
        requested_set = {ticker.upper() for ticker in requested or []}
        found = {match.group(0) for match in TICKER_PATTERN.finditer(text)}
        common_words = {"CEO", "CFO", "ETF", "USA", "SEC", "Fed".upper(), "AI", "IPO"}
        inferred = sorted((found - common_words) & requested_set) if requested_set else sorted(found - common_words)
        return inferred[:10]

    def _dedupe(self, items: list[NewsItem]) -> list[NewsItem]:
        seen: set[str] = set()
        deduped: list[NewsItem] = []
        for item in items:
            key = item.url.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped


news_service: BaseNewsService = RssNewsService(settings.news_rss_sources)
