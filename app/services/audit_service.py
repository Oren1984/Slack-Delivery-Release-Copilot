from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import audit_repo
from app.schemas.results import AuditEventOut


def list_audit_events(session: Session, release_id: str | None = None) -> list[AuditEventOut]:
    records = audit_repo.list_events(session, release_id=release_id)
    return [
        AuditEventOut(
            id=r.id,
            event_type=r.event_type,
            timestamp=r.timestamp,
            actor=r.actor,
            actor_role=r.actor_role,
            sprint_id=r.sprint_id,
            release_id=r.release_id,
            evidence_reference=r.evidence_reference,
            previous_state=r.previous_state,
            new_state=r.new_state,
            reason=r.reason,
            outcome=r.outcome,
            correlation_id=r.correlation_id,
        )
        for r in records
    ]
