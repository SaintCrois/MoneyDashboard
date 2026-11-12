"""Impact assessment API endpoints."""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.event import Event
from app.models.impact_assessment import ImpactAssessment
from app.schemas.assessment import AssessmentGenerateRequest, ImpactAssessmentOut
from app.services.impact_assessment_service import (
    generate_assessments_for_company,
    get_assessment,
    list_assessments,
)

router = APIRouter()


def _parse_json_field(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _assessment_to_out(a: ImpactAssessment, db: Session) -> ImpactAssessmentOut:
    company = db.query(Company).filter(Company.id == a.company_id).first()
    event = db.query(Event).filter(Event.id == a.event_id).first()
    return ImpactAssessmentOut(
        id=a.id,
        event_id=a.event_id,
        company_id=a.company_id,
        impact_type=a.impact_type,
        impact_severity=a.impact_severity,
        risk_level=a.risk_level,
        confidence=float(a.confidence) if a.confidence is not None else None,
        explanation=a.explanation,
        financial_exposure=a.financial_exposure,
        relevant_financial_metrics=_parse_json_field(a.relevant_financial_metrics),
        relevant_market_indicators=_parse_json_field(a.relevant_market_indicators),
        supporting_evidence=_parse_json_field(a.supporting_evidence),
        missing_information=_parse_json_field(a.missing_information),
        methodology=a.methodology,
        input_snapshot=_parse_json_field(a.input_snapshot),
        assessed_at=a.assessed_at,
        created_at=a.created_at,
        company_name=company.name if company else None,
        company_ticker=company.ticker if company else None,
        event_title=event.title if event else None,
        event_category=event.category if event else None,
    )


@router.get("/assessments", response_model=List[ImpactAssessmentOut])
def list_all_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all assessments with pagination."""
    assessments = list_assessments(db, skip=skip, limit=limit)
    return [_assessment_to_out(a, db) for a in assessments]


@router.get("/assessments/{assessment_id}", response_model=ImpactAssessmentOut)
def get_assessment_by_id(assessment_id: int, db: Session = Depends(get_db)):
    """Retrieve a single assessment by ID."""
    assessment = get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return _assessment_to_out(assessment, db)


@router.post("/assessments/generate", response_model=List[ImpactAssessmentOut], status_code=status.HTTP_201_CREATED)
def generate_assessment_endpoint(
    payload: AssessmentGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate impact assessment(s) for a company, optionally for a specific event."""
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if payload.event_id is not None:
        event = db.query(Event).filter(Event.id == payload.event_id).first()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    assessments = generate_assessments_for_company(db, company, event_id=payload.event_id)
    return [_assessment_to_out(a, db) for a in assessments]


@router.get("/companies/{company_id}/assessments", response_model=List[ImpactAssessmentOut])
def list_company_assessments(
    company_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List assessments for a specific company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    assessments = list_assessments(db, company_id=company_id, skip=skip, limit=limit)
    return [_assessment_to_out(a, db) for a in assessments]


@router.get("/events/{event_id}/assessments", response_model=List[ImpactAssessmentOut])
def list_event_assessments(
    event_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List assessments for a specific event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    assessments = list_assessments(db, event_id=event_id, skip=skip, limit=limit)
    return [_assessment_to_out(a, db) for a in assessments]
