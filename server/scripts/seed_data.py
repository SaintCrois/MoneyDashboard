"""Seed the database with illustrative reference data.

The seed is idempotent: re-running it will not create duplicate industries or
companies. It intentionally does not insert financial or market data.
"""

import os
import sys
from dotenv import load_dotenv

# Make the ``server`` directory importable as ``app`` so this script works both
# when run via ``python -m server.scripts.seed_data`` and directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.database import SessionLocal  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.industry import Industry  # noqa: E402

INDUSTRIES = ["Energy", "Tourism", "Petrochemicals"]

COMPANIES = [
    ("PTT", "PTT Public Company Limited", "Energy"),
    ("PTTEP", "PTTEP Public Company Limited", "Energy"),
    ("AOT", "Airports of Thailand Public Company Limited", "Tourism"),
    ("IVL", "Indorama Ventures Public Company Limited", "Petrochemicals"),
]


def seed(db) -> None:
    industry_map = {}
    for name in INDUSTRIES:
        industry = db.query(Industry).filter(Industry.name == name).first()
        if not industry:
            industry = Industry(name=name, description=None)
            db.add(industry)
            db.flush()
        industry_map[name] = industry

    for ticker, name, industry_name in COMPANIES:
        existing = (
            db.query(Company)
            .filter(Company.ticker == ticker)
            .filter((Company.market == "SET") | ((Company.market.is_(None)) & (Company.exchange == "SET")))
            .first()
        )
        if existing:
            continue
        company = Company(
            ticker=ticker,
            name=name,
            exchange="SET",
            market="SET",
            industry_id=industry_map[industry_name].id,
            description=None,
            source="seed",
        )
        db.add(company)

    db.commit()
    print("Seed data inserted.")


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
