"""Safe, non-destructive Sprint 2 schema migration.

Applies additive schema changes to an existing Sprint 1 database. Every change
is guarded so the script is idempotent and safe to re-run. No tables or data
are dropped or deleted.

Run after updating the SQLAlchemy models:

    python -m server.scripts.migrate_sprint2
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402


_STATEMENTS = [
    # NewsArticle: fetched_at timestamp
    (
        "news_articles_fetched_at",
        'ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS '
        "fetched_at TIMESTAMP WITH TIME ZONE",
    ),
    # Event: link to source article
    (
        "events_source_article_id",
        'ALTER TABLE events ADD COLUMN IF NOT EXISTS '
        "source_article_id INTEGER REFERENCES news_articles(id) ON DELETE SET NULL",
    ),
    # Event: classification metadata
    (
        "events_classification_method",
        'ALTER TABLE events ADD COLUMN IF NOT EXISTS '
        "classification_method VARCHAR(100)",
    ),
    (
        "events_confidence_score",
        'ALTER TABLE events ADD COLUMN IF NOT EXISTS '
        "confidence_score NUMERIC(5, 2)",
    ),
    (
        "events_processing_status",
        'ALTER TABLE events ADD COLUMN IF NOT EXISTS '
        "processing_status VARCHAR(50) NOT NULL DEFAULT 'processed'",
    ),
    # EventIndustry: relevance score
    (
        "event_industries_relevance_score",
        'ALTER TABLE event_industries ADD COLUMN IF NOT EXISTS '
        "relevance_score NUMERIC(5, 2)",
    ),
    # EventCompany: relevance score
    (
        "event_companies_relevance_score",
        'ALTER TABLE event_companies ADD COLUMN IF NOT EXISTS '
        "relevance_score NUMERIC(5, 2)",
    ),
]

# Unique constraints are applied separately because PostgreSQL does not support
# IF NOT EXISTS for ADD CONSTRAINT in all contexts; we catch failures instead.
_CONSTRAINTS = [
    (
        "uq_news_articles_url",
        'ALTER TABLE news_articles ADD CONSTRAINT uq_news_articles_url UNIQUE (url)',
    ),
]


def _execute(connection, label, sql) -> bool:
    try:
        connection.execute(text(sql))
        print(f"[applied] {label}")
        return True
    except Exception as exc:  # noqa: BLE001 - migration must not crash on partial state
        print(f"[skipped] {label}: {exc}")
        return False


def migrate() -> None:
    connection = engine.connect()
    connection = connection.execution_options(isolation_level="AUTOCOMMIT")
    try:
        for label, sql in _STATEMENTS:
            _execute(connection, label, sql)
        for label, sql in _CONSTRAINTS:
            _execute(connection, label, sql)
    finally:
        connection.close()
    print("Sprint 2 migration complete.")


if __name__ == "__main__":
    migrate()
