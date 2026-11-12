"""Event API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.event_industry import EventIndustry
from app.models.industry import Industry
from app.schemas.event import (
    CategoryOut,
    EventOut,
    EventProcessStats,
)
from app.schemas.mapping import EventCompanyDetail, EventIndustryDetail
from app.services.event_service import SUPPORTED_CATEGORIES, process_unprocessed_articles
from app.services.impact_mapping_service import map_event

router = APIRouter()


@router.get("/events/categories", response_model=List[CategoryOut])
def list_event_categories():
    """Retrieve the list of supported event categories."""
    return [CategoryOut(category=c) for c in SUPPORTED_CATEGORIES]


@router.get("/events", response_model=List[EventOut])
def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    category: Optional[str] = Query(None, description="Filter events by category"),
    db: Session = Depends(get_db),
):
    """Retrieve events, optionally filtered by category."""
    query = db.query(Event).options(joinedload(Event.source_article))
    if category:
        query = query.filter(Event.category == category)
    events = query.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Retrieve a single event by ID."""
    event = (
        db.query(Event)
        .options(joinedload(Event.source_article))
        .filter(Event.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.post("/events/process", response_model=EventProcessStats, status_code=status.HTTP_200_OK)
def process_events(db: Session = Depends(get_db)):
    """Process unprocessed news articles into structured events."""
    stats = process_unprocessed_articles(db)
    return stats


@router.get("/events/categories", response_model=List[CategoryOut])
def list_event_categories():
    """Retrieve the list of supported event categories."""
    return [CategoryOut(category=c) for c in SUPPORTED_CATEGORIES]


@router.get("/events/{event_id}/industries", response_model=List[EventIndustryDetail])
def get_event_industries(event_id: int, db: Session = Depends(get_db)):
    """Retrieve industries potentially affected by an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    mappings = (
        db.query(EventIndustry, Industry)
        .join(Industry, Industry.id == EventIndustry.industry_id)
        .filter(EventIndustry.event_id == event_id)
        .all()
    )
    return [
        EventIndustryDetail(
            id=m.id,
            event_id=m.event_id,
            industry_id=i.id,
            impact_type=m.impact_type,
            relevance_score=m.relevance_score,
            explanation=m.explanation,
            industry_name=i.name,
        )
        for m, i in mappings
    ]


@router.get("/events/{event_id}/companies", response_model=List[EventCompanyDetail])
def get_event_companies(event_id: int, db: Session = Depends(get_db)):
    """Retrieve companies potentially affected by an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    mappings = (
        db.query(EventCompany, Company)
        .join(Company, Company.id == EventCompany.company_id)
        .filter(EventCompany.event_id == event_id)
        .all()
    )
    return [
        EventCompanyDetail(
            id=m.id,
            event_id=m.event_id,
            company_id=c.id,
            impact_type=m.impact_type,
            exposure_type=m.exposure_type,
            relevance_score=m.relevance_score,
            explanation=m.explanation,
            company_name=c.name,
            ticker=c.ticker,
        )
        for m, c in mappings
    ]


@router.get("/companies/{company_id}/events", response_model=List[EventOut])
def get_company_events(
    company_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve events potentially affecting a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    events = (
        db.query(Event)
        .join(EventCompany, EventCompany.event_id == Event.id)
        .filter(EventCompany.company_id == company_id)
        .options(joinedload(Event.source_article))
        .all()
    )
    return events


def ensure_event_mapped(db: Session, event_id: int) -> None:
    """Map an event to industries and companies if not already mapped."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return
    has_industry = (
        db.query(EventIndustry)
        .filter(EventIndustry.event_id == event_id)
        .first()
    )
    has_company = (
        db.query(EventCompany)
        .filter(EventCompany.event_id == event_id)
        .first()
    )
    if not has_industry or not has_company:
        map_event(db, event)

__all__ = ["router", "ensure_event_mapped"]
