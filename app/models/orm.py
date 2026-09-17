from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class GateEvaluationRecord(Base):
    """One row per gate evaluation. Never updated or deleted — a release can
    be re-evaluated after data changes, producing a new row, so history of
    every evaluation stays visible.
    """

    __tablename__ = "gate_evaluations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    release_id: Mapped[str] = mapped_column(String(64), index=True)
    sprint_id: Mapped[str] = mapped_column(String(64), index=True)
    gate_status: Mapped[str] = mapped_column(String(32))
    payload_json: Mapped[dict] = mapped_column(JSON)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    correlation_id: Mapped[str] = mapped_column(String(32))


class HumanDecisionRecord(Base):
    """Append-only ledger of every approval/hold attempt (accepted or
    rejected). Decisions are never updated in place — a later decision is a
    new row, so the full history remains visible in the audit trail.
    """

    __tablename__ = "human_decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    release_id: Mapped[str] = mapped_column(String(64), index=True)
    sprint_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted: Mapped[bool] = mapped_column(default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    correlation_id: Mapped[str] = mapped_column(String(32))


class AuditEventRecord(Base):
    """Append-only audit trail. The application layer never issues UPDATE or
    DELETE against this table.
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sprint_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    release_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    evidence_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    previous_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(String(32))
    correlation_id: Mapped[str] = mapped_column(String(32))


class CloseoutReportRecord(Base):
    __tablename__ = "closeout_reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    sprint_id: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
