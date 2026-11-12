"""Initialize the database by creating all SQLAlchemy tables.

This is idempotent and non-destructive: it only creates tables that do not
already exist. It never drops or deletes existing tables or data.
"""

import os
import sys
from dotenv import load_dotenv

# Make the ``server`` directory importable as ``app`` so this script works both
# when run via ``python -m server.scripts.init_db`` and directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: F401  (registers all models with Base.metadata)


def init_db() -> None:
    """Create all tables defined on ``Base.metadata``."""
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
