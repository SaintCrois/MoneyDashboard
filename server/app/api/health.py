"""Health API endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Return the backend availability status."""
    return {"status": "ok"}
