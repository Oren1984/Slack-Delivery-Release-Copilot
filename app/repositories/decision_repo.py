from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_correlation_id
from app.models.orm import HumanDecisionRecord


def add_decision(
    session: Session,
    *,
    release_id: str,
    sprint_id: str,
    actor: str,
    role: str,
    decision: str,
    reason: str | None,
    accepted: bool,
    rejection_reason: str | None,
) -> HumanDecisionRecord:
    record = HumanDecisionRecord(
        release_id=release_id,
        sprint_id=sprint_id,
        actor=actor,
        role=role,
        decision=decision,
        reason=reason,
        accepted=accepted,
        rejection_reason=rejection_reason,
        correlation_id=get_correlation_id(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_decisions(session: Session, release_id: str) -> list[HumanDecisionRecord]:
    stmt = (
        select(HumanDecisionRecord)
        .where(HumanDecisionRecord.release_id == release_id)
        .order_by(HumanDecisionRecord.timestamp.asc())
    )
    return list(session.execute(stmt).scalars().all())


def get_accepted_decision(session: Session, release_id: str) -> HumanDecisionRecord | None:
    """Returns the first accepted (non-rejected) decision for a release, if
    any. Once an accepted decision exists, further decision attempts must be
    rejected as duplicates rather than silently overwriting it.
    """
    decisions = list_decisions(session, release_id)
    for record in decisions:
        if record.accepted:
            return record
    return None
