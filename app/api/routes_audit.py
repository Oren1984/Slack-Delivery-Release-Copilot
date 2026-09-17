from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.schemas.results import AuditEventOut
from app.services.audit_service import list_audit_events

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
def get_all_audit_events(session: Session = Depends(get_session)) -> list[AuditEventOut]:
    return list_audit_events(session)


@router.get("/{release_id}", response_model=list[AuditEventOut])
def get_audit_events_for_release(
    release_id: str, session: Session = Depends(get_session)
) -> list[AuditEventOut]:
    return list_audit_events(session, release_id=release_id)
