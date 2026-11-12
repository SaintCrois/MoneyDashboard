"""Safe, non-destructive schema migration for SET sync, news relevance, and matching.

Applies additive schema changes to an existing database. Every change is
guarded so the script is idempotent and safe to re-run. No tables or data
are dropped or deleted except replacing ticker-only uniqueness to support
ticker+market deduplication when safe.

Run:

    python -m server.scripts.migrate_news_matching
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402


_COLUMN_STATEMENTS = [
    # --- Company: SET/listing fields (additive) ---
    ("companies_market", "ALTER TABLE companies ADD COLUMN IF NOT EXISTS market VARCHAR(100)"),
    ("companies_sector", "ALTER TABLE companies ADD COLUMN IF NOT EXISTS sector VARCHAR(255)"),
    ("companies_source", "ALTER TABLE companies ADD COLUMN IF NOT EXISTS source VARCHAR(255)"),
    ("companies_last_synced_at", "ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE"),

    # --- NewsArticle: relevance/language ---
    ("news_articles_thailand_relevance", "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS thailand_relevance VARCHAR(50)"),
    ("news_articles_relevance_reason", "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS relevance_reason TEXT"),
    ("news_articles_language", "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS language VARCHAR(20)"),

    # --- EventCompany: traceable matching evidence ---
    ("event_companies_match_confidence", "ALTER TABLE event_companies ADD COLUMN IF NOT EXISTS match_confidence VARCHAR(20)"),
    ("event_companies_match_reason", "ALTER TABLE event_companies ADD COLUMN IF NOT EXISTS match_reason TEXT"),
    ("event_companies_evidence", "ALTER TABLE event_companies ADD COLUMN IF NOT EXISTS evidence TEXT"),
    ("event_companies_created_at", "ALTER TABLE event_companies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
]

_TABLE_STATEMENTS = [
    ("news_source_status_table",
     """CREATE TABLE IF NOT EXISTS news_source_status (
        id SERIAL PRIMARY KEY,
        source_name VARCHAR(255) NOT NULL UNIQUE,
        feed_url VARCHAR(2000),
        http_status INTEGER,
        content_type VARCHAR(255),
        parsed_count INTEGER DEFAULT 0,
        inserted_count INTEGER DEFAULT 0,
        duplicate_count INTEGER DEFAULT 0,
        error_message TEXT,
        final_status VARCHAR(50),
        last_successful_ingestion_at TIMESTAMP WITH TIME ZONE,
        last_checked_at TIMESTAMP WITH TIME ZONE
    )"""),
]


def _execute(connection, label, sql) -> bool:
    try:
        connection.execute(text(sql))
        print(f"[applied] {label}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[skipped] {label}: {exc}")
        return False


def migrate() -> None:
    connection = engine.connect()
    connection = connection.execution_options(isolation_level="AUTOCOMMIT")
    try:
        for label, sql in _COLUMN_STATEMENTS:
            _execute(connection, label, sql)
        for label, sql in _TABLE_STATEMENTS:
            _execute(connection, label, sql)

        # Backfill company market from exchange where missing
        _execute(connection, "companies_backfill_market",
                 "UPDATE companies SET market = exchange WHERE market IS NULL AND exchange IS NOT NULL")

        # Replace global ticker uniqueness with (ticker, market) uniqueness when possible.
        for cname in ("companies_ticker_key", "uq_companies_ticker", "companies_ticker_unique"):
            _execute(connection, f"drop_constraint_{cname}", f"ALTER TABLE companies DROP CONSTRAINT IF EXISTS {cname}")
        _execute(connection, "drop_index_ix_companies_ticker", "DROP INDEX IF EXISTS ix_companies_ticker")
        _execute(connection, "drop_index_companies_ticker_key", "DROP INDEX IF EXISTS companies_ticker_key")
        _execute(connection, "ix_companies_ticker", "CREATE INDEX IF NOT EXISTS ix_companies_ticker ON companies(ticker)")
        _execute(connection, "uq_company_ticker_market",
                 "CREATE UNIQUE INDEX IF NOT EXISTS uq_company_ticker_market ON companies (ticker, COALESCE(market, exchange, ''))")

    finally:
        connection.close()
    print("News/matching migration complete.")


if __name__ == "__main__":
    migrate()
