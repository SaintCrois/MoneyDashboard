"""Safe, non-destructive Sprint 3 schema migration.

Applies additive schema changes to an existing database. Every change is
guarded so the script is idempotent and safe to re-run. No tables or data
are dropped or deleted.

Run after updating the SQLAlchemy models:

    python -m server.scripts.migrate_sprint3
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402


_STATEMENTS = [
    # --- FinancialData (Sprint 3 additive fields) ---
    ("financial_data_reporting_period",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS reporting_period VARCHAR(50)'),
    ("financial_data_operating_income",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS operating_income NUMERIC(20, 2)'),
    ("financial_data_total_assets",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS total_assets NUMERIC(20, 2)'),
    ("financial_data_total_liabilities",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS total_liabilities NUMERIC(20, 2)'),
    ("financial_data_total_debt",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS total_debt NUMERIC(20, 2)'),
    ("financial_data_shareholders_equity",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS shareholders_equity NUMERIC(20, 2)'),
    ("financial_data_operating_cash_flow",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS operating_cash_flow NUMERIC(20, 2)'),
    ("financial_data_capital_expenditure",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS capital_expenditure NUMERIC(20, 2)'),
    ("financial_data_eps",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS eps NUMERIC(20, 4)'),
    ("financial_data_revenue_growth",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS revenue_growth NUMERIC(10, 4)'),
    ("financial_data_data_source",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS data_source VARCHAR(255)'),
    ("financial_data_reported_at",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS reported_at TIMESTAMP WITH TIME ZONE'),
    ("financial_data_is_estimate",
     'ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS is_estimate BOOLEAN NOT NULL DEFAULT FALSE'),

    # --- MarketData (Sprint 3 additive fields) ---
    ("market_data_open_price",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS open_price NUMERIC(20, 4)'),
    ("market_data_high_price",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS high_price NUMERIC(20, 4)'),
    ("market_data_low_price",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS low_price NUMERIC(20, 4)'),
    ("market_data_close_price",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS close_price NUMERIC(20, 4)'),
    ("market_data_daily_change_pct",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS daily_change_pct NUMERIC(10, 4)'),
    ("market_data_data_source",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS data_source VARCHAR(255)'),
    ("market_data_is_delayed",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS is_delayed BOOLEAN NOT NULL DEFAULT FALSE'),
    ("market_data_is_estimate",
     'ALTER TABLE market_data ADD COLUMN IF NOT EXISTS is_estimate BOOLEAN NOT NULL DEFAULT FALSE'),

    # --- ImpactAssessment (Sprint 3 additive fields) ---
    ("impact_assessments_impact_severity",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS impact_severity VARCHAR(20) DEFAULT \'Unknown\''),
    ("impact_assessments_financial_exposure",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS financial_exposure TEXT'),
    ("impact_assessments_relevant_financial_metrics",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS relevant_financial_metrics TEXT'),
    ("impact_assessments_relevant_market_indicators",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS relevant_market_indicators TEXT'),
    ("impact_assessments_supporting_evidence",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS supporting_evidence TEXT'),
    ("impact_assessments_missing_information",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS missing_information TEXT'),
    ("impact_assessments_methodology",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS methodology VARCHAR(255)'),
    ("impact_assessments_input_snapshot",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS input_snapshot TEXT'),
    ("impact_assessments_assessed_at",
     'ALTER TABLE impact_assessments ADD COLUMN IF NOT EXISTS assessed_at TIMESTAMP WITH TIME ZONE'),
]

_CONSTRAINTS = [
    (
        "uq_company_recorded_at",
        'ALTER TABLE market_data ADD CONSTRAINT uq_company_recorded_at UNIQUE (company_id, recorded_at)',
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
    print("Sprint 3 migration complete.")


if __name__ == "__main__":
    migrate()
