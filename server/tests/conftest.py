"""Pytest configuration for the backend test suite.

Adds the ``server`` directory to ``sys.path`` so that ``app`` resolves as a
top-level package (matching how ``server/scripts/init_db.py`` imports it), and
ensures all SQLAlchemy tables exist (idempotent, non-destructive).

Test isolation
--------------
Every test receives a ``db`` session bound to a short-lived database
transaction. The session's ``commit()`` is replaced with ``flush()`` so that
services can commit their work within the test without permanently writing to
the development database. The transaction is rolled back when the test ends,
leaving the development database untouched. This satisfies the requirement to
never run destructive tests against the user's development database.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.database import Base, engine, SessionLocal  # noqa: E402

# Create all tables once for the test session. Idempotent: never drops or
# deletes existing tables or data.
Base.metadata.create_all(bind=engine)


import pytest  # noqa: E402


@pytest.fixture
def db():
    """Provide an isolated, rolled-back database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    # Let services call commit() without permanently writing: treat commit as
    # flush within the rolled-back transaction.
    session.commit = session.flush
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    """Provide a FastAPI TestClient whose get_db uses the isolated session."""
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402
    from app.database import get_db  # noqa: E402

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
