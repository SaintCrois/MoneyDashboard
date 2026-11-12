"""News ingestion service.

Collects news articles from configured sources (RSS feeds), normalizes them,
and stores them in PostgreSQL. Duplicate articles are prevented using a unique
constraint on the normalized article URL. Source failures are logged and do not
abort the ingestion of other sources.

No external API keys are required. External sources are optional: if all sources
are unavailable, the application continues to work with stored articles.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle
from app.services.news_sources import DEFAULT_SOURCES, NewsSource

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 15


def _normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a URL so duplicates are detected consistently."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    # Strip tracking/query noise and trailing slash for stable dedup.
    if "?" in url:
        url = url.split("?", 1)[0]
    if url.endswith("/"):
        url = url[:-1]
    return url or None


def _parse_rss_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse common RSS date formats into a timezone-aware datetime."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _fetch_rss(url: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> str:
    """Fetch the raw RSS XML from a source URL."""
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_rss_feed(xml_text: str, source_name: str) -> List[dict]:
    """Parse RSS XML into a list of normalized article dicts."""
    articles: List[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("Failed to parse RSS feed %s: %s", source_name, exc)
        return articles

    items = root.findall(".//item")
    for item in items:
        def _text(tag: str) -> Optional[str]:
            element = item.find(tag)
            if element is None or element.text is None:
                return None
            return element.text.strip()

        title = _text("title")
        url = _normalize_url(_text("link"))
        summary = _text("description")
        published_at = _parse_rss_datetime(_text("pubDate"))

        if not title or not url:
            continue

        articles.append(
            {
                "title": title[:500],
                "source": source_name,
                "url": url,
                "published_at": published_at,
                "summary": summary,
                "content": None,
                "fetched_at": datetime.now(timezone.utc),
            }
        )
    return articles


def ingest_articles(
    db: Session,
    sources: Optional[List[NewsSource]] = None,
) -> dict:
    """Ingest articles from configured sources into the database.

    Returns a stats dict with counts of ingested, skipped (duplicates), and
    errored articles plus per-source results.
    """
    if sources is None:
        sources = DEFAULT_SOURCES

    stats = {
        "ingested": 0,
        "skipped_duplicate": 0,
        "errors": 0,
        "sources": [],
    }

    for source in sources:
        if not source.enabled:
            continue
        source_result = {
            "name": source.name,
            "url": source.url,
            "type": source.source_type,
            "ingested": 0,
            "skipped": 0,
            "error": None,
        }

        try:
            if source.source_type == "rss":
                xml_text = _fetch_rss(source.url)
                parsed = _parse_rss_feed(xml_text, source.name)
            else:
                logger.warning(
                    "Unsupported source type %s for %s", source.source_type, source.name
                )
                parsed = []

            for article in parsed:
                existing = (
                    db.query(NewsArticle)
                    .filter(NewsArticle.url == article["url"])
                    .first()
                )
                if existing:
                    stats["skipped_duplicate"] += 1
                    source_result["skipped"] += 1
                    continue

                record = NewsArticle(**article)
                db.add(record)
                db.flush()
                stats["ingested"] += 1
                source_result["ingested"] += 1

            db.commit()

        except (URLError, HTTPError, OSError, ET.ParseError) as exc:
            db.rollback()
            logger.error("Ingestion error for source %s: %s", source.name, exc)
            stats["errors"] += 1
            stats["sources"].append(
                {
                    **source_result,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        except Exception as exc:  # noqa: BLE001 - never crash the whole pipeline
            db.rollback()
            logger.exception("Unexpected ingestion error for source %s", source.name)
            stats["errors"] += 1
            stats["sources"].append(
                {
                    **source_result,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        stats["sources"].append(source_result)

    return stats

__all__ = ["ingest_articles", "_normalize_url", "_parse_rss_feed"]
