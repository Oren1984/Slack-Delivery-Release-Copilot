from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_correlation_id
from app.models.orm import GateEvaluationRecord
from app.schemas.results import GateEvaluationResult


def save_evaluation(session: Session, result: GateEvaluationResult) -> GateEvaluationRecord:
    record = GateEvaluationRecord(
        release_id=result.release_id,
        sprint_id="",
        gate_status=result.gate_status.value,
        payload_json=result.model_dump(mode="json"),
        evaluated_at=result.evaluated_at,
        correlation_id=get_correlation_id(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_latest_evaluation(session: Session, release_id: str) -> GateEvaluationRecord | None:
    stmt = (
        select(GateEvaluationRecord)
        .where(GateEvaluationRecord.release_id == release_id)
        .order_by(GateEvaluationRecord.evaluated_at.desc())
    )
    return session.execute(stmt).scalars().first()
