from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import CloseoutReportRecord
from app.schemas.results import CloseoutReport


def save_report(session: Session, sprint_id: str, report: CloseoutReport) -> CloseoutReportRecord:
    record = CloseoutReportRecord(sprint_id=sprint_id, payload_json=report.model_dump(mode="json"))
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_latest_report(session: Session, sprint_id: str) -> CloseoutReportRecord | None:
    stmt = (
        select(CloseoutReportRecord)
        .where(CloseoutReportRecord.sprint_id == sprint_id)
        .order_by(CloseoutReportRecord.generated_at.desc())
    )
    return session.execute(stmt).scalars().first()
