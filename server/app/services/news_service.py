"""News ingestion service.

Collects news articles from configured sources (RSS and Atom feeds), normalizes
them, classifies Thailand relevance, and stores them in PostgreSQL. Duplicate
articles are prevented using a unique constraint on the normalized article URL.
Source failures are logged and do not abort the ingestion of other sources.

No external API keys are required. External sources are optional: if sources
are unavailable, the application continues to work with stored articles.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle
from app.services.news_sources import NewsSource, get_configured_sources
from app.services.thailand_relevance_service import classify_thailand_relevance

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 15
REQUEST_HEADERS = {
    "User-Agent": "AI-Investment-Radar/1.0 (news ingestion; no auth required)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

ATOM_NS = "{http://www.w3.org/2005/Atom}"


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
    """Parse common RSS/Atom date formats into a timezone-aware datetime."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
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


def _strip_html(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    # lightweight tag removal for summaries
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _detect_language(title: Optional[str], summary: Optional[str]) -> str:
    """Best-effort language hint (English-focused pipeline)."""
    text = f"{title or ''} {summary or ''}"
    # Thai script range indicates Thai content.
    if re.search(r"[\u0E00-\u0E7F]", text):
        return "th"
    # Default to English for configured English feeds.
    return "en"


def _fetch_feed(url: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    """Fetch the raw feed XML from a source URL with appropriate headers.

    Returns a dict with ``body`` (str), ``http_status`` (int | None), and
    ``content_type`` (str | None).
    """
    req = Request(url, headers=REQUEST_HEADERS)
    with urlopen(req, timeout=timeout) as response:
        status = getattr(response, "status", None)
        if status is None and hasattr(response, "getcode"):
            status = response.getcode()
        headers = getattr(response, "headers", None)
        content_type = headers.get("Content-Type") if headers else None
        body = response.read().decode("utf-8", errors="replace")
        return {"body": body, "http_status": status, "content_type": content_type}


def _atom_link(element) -> Optional[str]:
    """Extract an href from an Atom link element."""
    if element is None:
        return None
    href = element.get("href")
    if href:
        return href
    text = (element.text or "").strip()
    return text or None


def _parse_rss_feed(xml_text: str, source_name: str, source_language: str = "en") -> List[dict]:
    """Parse RSS 2.0 or Atom XML into a list of normalized article dicts.

    Handles invalid XML, empty feeds, missing publication dates, and
    malformed entries without raising.
    """
    articles: List[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("Failed to parse feed %s: %s", source_name, exc)
        return articles

    tag = root.tag.lower()
    items = root.findall(".//item")

    if items:
        # RSS 2.0
        for item in items:
            def _text(tag_name: str) -> Optional[str]:
                element = item.find(tag_name)
                if element is None or element.text is None:
                    return None
                return element.text.strip()

            title = _text("title")
            url = _normalize_url(_text("link"))
            summary = _strip_html(_text("description"))
            published_at = _parse_rss_datetime(_text("pubDate"))

            if not title or not url:
                continue

            language = source_language or _detect_language(title, summary)
            relevance = classify_thailand_relevance(title, summary, None)
            articles.append(
                {
                    "title": title[:500],
                    "source": source_name,
                    "url": url,
                    "published_at": published_at,
                    "summary": summary,
                    "content": None,
                    "fetched_at": datetime.now(timezone.utc),
                    "thailand_relevance": relevance.classification,
                    "relevance_reason": relevance.reason,
                    "language": language,
                }
            )
    elif tag.endswith("feed") or root.findall(".//" + ATOM_NS + "entry"):
        # Atom
        entries = root.findall(".//" + ATOM_NS + "entry")
        for entry in entries:
            def _atom_text(tag_name: str) -> Optional[str]:
                element = entry.find(tag_name)
                if element is None or element.text is None:
                    return None
                return element.text.strip()

            title = _atom_text(ATOM_NS + "title")
            link_element = entry.find(ATOM_NS + "link")
            url = _normalize_url(_atom_link(link_element))
            summary = _strip_html(_atom_text(ATOM_NS + "summary"))
            published_at = _parse_rss_datetime(_atom_text(ATOM_NS + "published"))
            if not published_at:
                published_at = _parse_rss_datetime(_atom_text(ATOM_NS + "updated"))

            if not title or not url:
                continue

            language = source_language or _detect_language(title, summary)
            relevance = classify_thailand_relevance(title, summary, None)
            articles.append(
                {
                    "title": title[:500],
                    "source": source_name,
                    "url": url,
                    "published_at": published_at,
                    "summary": summary,
                    "content": None,
                    "fetched_at": datetime.now(timezone.utc),
                    "thailand_relevance": relevance.classification,
                    "relevance_reason": relevance.reason,
                    "language": language,
                }
            )
    else:
        logger.warning("Feed %s is not a recognized RSS or Atom feed", source_name)

    return articles


def _record_source_status(db: Session, source_result: dict) -> None:
    """Persist per-source ingestion status for UI/history (best-effort)."""
    try:
        now = datetime.now(timezone.utc)
        last_success = None
        if source_result.get("final_status") == "Success":
            last_success = now
        sql = text(
            """
            INSERT INTO news_source_status (
                source_name, feed_url, http_status, content_type,
                parsed_count, inserted_count, duplicate_count, error_message,
                final_status, last_successful_ingestion_at, last_checked_at
            ) VALUES (
                :source_name, :feed_url, :http_status, :content_type,
                :parsed_count, :inserted_count, :duplicate_count, :error_message,
                :final_status, :last_successful_ingestion_at, :last_checked_at
            )
            ON CONFLICT (source_name) DO UPDATE SET
                feed_url = EXCLUDED.feed_url,
                http_status = EXCLUDED.http_status,
                content_type = EXCLUDED.content_type,
                parsed_count = EXCLUDED.parsed_count,
                inserted_count = EXCLUDED.inserted_count,
                duplicate_count = EXCLUDED.duplicate_count,
                error_message = EXCLUDED.error_message,
                final_status = EXCLUDED.final_status,
                last_successful_ingestion_at = COALESCE(EXCLUDED.last_successful_ingestion_at, news_source_status.last_successful_ingestion_at),
                last_checked_at = EXCLUDED.last_checked_at
            """
        )
        db.execute(
            sql,
            {
                "source_name": source_result.get("name"),
                "feed_url": source_result.get("url"),
                "http_status": source_result.get("http_status"),
                "content_type": source_result.get("content_type"),
                "parsed_count": int(source_result.get("parsed") or 0),
                "inserted_count": int(source_result.get("ingested") or 0),
                "duplicate_count": int(source_result.get("skipped") or 0),
                "error_message": source_result.get("error"),
                "final_status": source_result.get("final_status"),
                "last_successful_ingestion_at": last_success,
                "last_checked_at": now,
            },
        )
        db.commit()
        source_result["last_successful_ingestion_at"] = (
            last_success.isoformat() if last_success else source_result.get("last_successful_ingestion_at")
        )
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("Failed to persist news source status for %s", source_result.get("name"))


def _fetch_feeds_parallel(sources) -> dict:
    """Fetch enabled RSS sources concurrently. Maps url -> fetch dict or the raised exception."""
    targets = [
        s.url for s in sources
        if getattr(s, "enabled", True) and s.url and s.source_type == "rss"
    ]

    def _safe_fetch(url: str):
        try:
            return _fetch_feed(url)
        except Exception as exc:  # noqa: BLE001 - re-raised per source by the caller
            return exc

    if not targets:
        return {}
    with ThreadPoolExecutor(max_workers=min(8, len(targets))) as pool:
        return dict(zip(targets, pool.map(_safe_fetch, targets)))


def ingest_articles(
    db: Session,
    sources: Optional[List[NewsSource]] = None,
) -> dict:
    """Ingest articles from configured sources into the database.

    Returns a stats dict with counts and per-source results.
    """
    if sources is None:
        sources = get_configured_sources()

    stats = {
        "ingested": 0,
        "skipped_duplicate": 0,
        "errors": 0,
        "status": "No Articles",
        "sources": [],
    }

    # Fetch every enabled RSS feed in parallel; results are stored one source
    # at a time below so database writes stay on this thread.
    fetched = _fetch_feeds_parallel(sources)

    for source in sources:
        source_result = {
            "name": source.name,
            "publisher": getattr(source, "publisher", source.name),
            "url": source.url,
            "type": source.source_type,
            "http_status": None,
            "content_type": None,
            "ingested": 0,
            "skipped": 0,
            "parsed": 0,
            "error": None,
            "final_status": "Failed",
            "last_successful_ingestion_at": None,
        }

        # Disabled/unavailable sources (e.g. no verified accessible feed) must be
        # recorded explicitly, not fabricated or silently treated as success.
        if not getattr(source, "enabled", True) or not source.url:
            source_result["final_status"] = "Unavailable"
            source_result["error"] = getattr(source, "notes", None) or "Source unavailable (no verified accessible feed)."
            _record_source_status(db, source_result)
            stats["sources"].append(source_result)
            continue

        try:
            if source.source_type == "rss":
                fetch = fetched[source.url]
                if isinstance(fetch, Exception):
                    raise fetch
                source_result["http_status"] = fetch.get("http_status")
                source_result["content_type"] = fetch.get("content_type")
                parsed = _parse_rss_feed(
                    fetch.get("body", ""),
                    source.name,
                    source_language=getattr(source, "language", "en") or "en",
                )
            else:
                logger.warning("Unsupported source type %s for %s", source.source_type, source.name)
                parsed = []

            source_result["parsed"] = len(parsed)

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

            # Do not report success merely because of HTTP 200.
            if source_result["parsed"] == 0:
                source_result["final_status"] = "No Articles"
            elif source_result["ingested"] > 0 or source_result["skipped"] > 0:
                source_result["final_status"] = "Success"
            else:
                source_result["final_status"] = "No Articles"

        except (URLError, HTTPError, OSError, ET.ParseError) as exc:
            db.rollback()
            logger.error("Ingestion error for source %s: %s", source.name, exc)
            stats["errors"] += 1
            if isinstance(exc, HTTPError):
                source_result["http_status"] = exc.code
                ct = exc.headers.get("Content-Type") if exc.headers else None
                source_result["content_type"] = ct
            source_result["error"] = f"{type(exc).__name__}: {exc}"
            source_result["final_status"] = "Failed"
            _record_source_status(db, source_result)
            stats["sources"].append(source_result)
            continue
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.exception("Unexpected ingestion error for source %s", source.name)
            stats["errors"] += 1
            source_result["error"] = f"{type(exc).__name__}: {exc}"
            source_result["final_status"] = "Failed"
            _record_source_status(db, source_result)
            stats["sources"].append(source_result)
            continue

        _record_source_status(db, source_result)
        stats["sources"].append(source_result)

    # Compute overall status after processing all sources.
    success_like = any(s.get("final_status") == "Success" for s in stats["sources"])
    no_articles_like = any(s.get("final_status") == "No Articles" for s in stats["sources"])
    failures = any(s.get("final_status") in ("Failed", "Unavailable") for s in stats["sources"])

    if failures and success_like:
        stats["status"] = "Partial Success"
    elif failures and not success_like and not no_articles_like and stats["ingested"] == 0 and stats["skipped_duplicate"] == 0:
        stats["status"] = "Failed"
    elif stats["ingested"] == 0 and stats["skipped_duplicate"] == 0 and not success_like:
        # includes No Articles / Unavailable-only runs
        stats["status"] = "No Articles" if not failures else "Failed"
    else:
        stats["status"] = "Success"

    return stats


__all__ = ["ingest_articles", "_normalize_url", "_parse_rss_feed"]

