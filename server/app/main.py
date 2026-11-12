from fastapi import FastAPI

from app.database import Base, engine
import app.models  # noqa: F401  (registers all models with Base.metadata)
from app.api import health, companies, industries

app = FastAPI(
    title="AI Investment Impact Radar",
    description="Global events and investment impact analysis API",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    """Create all SQLAlchemy tables on startup (idempotent, non-destructive)."""
    Base.metadata.create_all(bind=engine)


app.include_router(health.router)
app.include_router(companies.router, prefix="/api")
app.include_router(industries.router, prefix="/api")
