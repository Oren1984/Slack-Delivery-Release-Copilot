from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_correlation_id
from app.models.orm import AuditEventRecord


def append_event(
    session: Session,
    *,
    event_type: str,
    outcome: str,
    actor: str | None = None,
    actor_role: str | None = None,
    sprint_id: str | None = None,
    release_id: str | None = None,
    evidence_reference: str | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    reason: str | None = None,
) -> AuditEventRecord:
    """Append one audit event. This is the only write path onto the audit
    table — the application never issues UPDATE or DELETE against it, so the
    trail is append-only at the application level.
    """
    record = AuditEventRecord(
        event_type=event_type,
        outcome=outcome,
        actor=actor,
        actor_role=actor_role,
        sprint_id=sprint_id,
        release_id=release_id,
        evidence_reference=evidence_reference,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason,
        correlation_id=get_correlation_id(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_events(session: Session, release_id: str | None = None) -> list[AuditEventRecord]:
    stmt = select(AuditEventRecord).order_by(AuditEventRecord.timestamp.desc())
    if release_id is not None:
        stmt = stmt.where(AuditEventRecord.release_id == release_id)
    return list(session.execute(stmt).scalars().all())
