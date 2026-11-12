"""Pytest configuration for the backend test suite.

Adds the ``server`` directory to ``sys.path`` so that ``app`` resolves as a
top-level package (matching how ``server/scripts/init_db.py`` imports it), and
ensures all SQLAlchemy tables exist (idempotent, non-destructive).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.database import Base, engine  # noqa: E402

# Create all tables once for the test session. Idempotent: never drops or
# deletes existing tables or data.
Base.metadata.create_all(bind=engine)
