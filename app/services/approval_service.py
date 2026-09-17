from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import (
    DuplicateDecisionError,
    InvalidReleaseTransitionError,
    MissingEvidenceError,
    UnauthorizedDecisionError,
)
from app.core.metrics import (
    rejected_approval_attempts_total,
    release_approvals_total,
    release_holds_total,
)
from app.repositories import audit_repo, decision_repo
from app.schemas.dataset import ScenarioDataset
from app.schemas.enums import DecisionType, GateStatus, Role
from app.schemas.results import DecisionRecord, GateEvaluationResult
from app.services import audit_events
from app.services.governance import actor_has_role, is_authorized_to_decide


def submit_decision(
    session: Session,
    dataset: ScenarioDataset,
    gate_result: GateEvaluationResult | None,
    *,
    actor: str,
    role: Role,
    decision: DecisionType,
    reason: str | None,
) -> DecisionRecord:
    """Human approval/hold state machine.

    - Only an authorized role, registered under that exact role for this
      scenario, may submit a decision.
    - Every attempt (accepted or rejected) is recorded and audited.
    - Once a release has an accepted decision, further attempts are
      rejected as duplicates rather than silently overwriting it.
    - APPROVED requires a prior gate evaluation with status
      READY_FOR_HUMAN_APPROVAL; missing evidence or unresolved blockers
      reject the approval outright.
    - HELD is always permitted for an authorized actor, with an optional
      reason, regardless of gate status.
    """
    release_id = dataset.release_candidate.id
    sprint_id = dataset.sprint.id

    audit_repo.append_event(
        session,
        event_type=audit_events.APPROVAL_ATTEMPTED,
        outcome="attempted",
        actor=actor,
        actor_role=role.value,
        sprint_id=sprint_id,
        release_id=release_id,
        new_state=decision.value,
        reason=reason,
    )

    def _reject(exc: Exception, rejection_reason: str) -> None:
        rejected_approval_attempts_total.inc()
        decision_repo.add_decision(
            session,
            release_id=release_id,
            sprint_id=sprint_id,
            actor=actor,
            role=role.value,
            decision=decision.value,
            reason=reason,
            accepted=False,
            rejection_reason=rejection_reason,
        )
        audit_repo.append_event(
            session,
            event_type=audit_events.APPROVAL_REJECTED,
            outcome=rejection_reason,
            actor=actor,
            actor_role=role.value,
            sprint_id=sprint_id,
            release_id=release_id,
            new_state=decision.value,
            reason=rejection_reason,
        )
        raise exc

    if not is_authorized_to_decide(role):
        _reject(
            UnauthorizedDecisionError(
                f"Role '{role.value}' is not authorized to approve or hold a release."
            ),
            "unauthorized_role",
        )

    if not actor_has_role(dataset.authorized_actors, actor, role):
        _reject(
            UnauthorizedDecisionError(
                f"Actor '{actor}' is not registered under role '{role.value}' for this scenario."
            ),
            "actor_role_mismatch",
        )

    existing = decision_repo.get_accepted_decision(session, release_id)
    if existing is not None:
        _reject(
            DuplicateDecisionError(
                f"Release '{release_id}' already has a recorded decision "
                f"({existing.decision} by {existing.actor})."
            ),
            "duplicate_decision",
        )

    if decision == DecisionType.APPROVED:
        if gate_result is None:
            _reject(
                InvalidReleaseTransitionError(
                    "No release gate evaluation is on record; evaluate the gate before approving."
                ),
                "no_gate_evaluation",
            )
        elif gate_result.gate_status == GateStatus.INSUFFICIENT_EVIDENCE:
            _reject(
                MissingEvidenceError(
                    "Required release evidence is missing; approval is blocked until "
                    "it is supplied."
                ),
                "missing_evidence",
            )
        elif gate_result.gate_status != GateStatus.READY_FOR_HUMAN_APPROVAL:
            _reject(
                InvalidReleaseTransitionError(
                    f"Release gate status is '{gate_result.gate_status.value}'; "
                    "approval requires READY_FOR_HUMAN_APPROVAL."
                ),
                "gate_not_ready",
            )

    record = decision_repo.add_decision(
        session,
        release_id=release_id,
        sprint_id=sprint_id,
        actor=actor,
        role=role.value,
        decision=decision.value,
        reason=reason,
        accepted=True,
        rejection_reason=None,
    )

    if decision == DecisionType.APPROVED:
        release_approvals_total.inc()
        event_type = audit_events.RELEASE_APPROVED
    else:
        release_holds_total.inc()
        event_type = audit_events.RELEASE_HELD

    audit_repo.append_event(
        session,
        event_type=event_type,
        outcome="accepted",
        actor=actor,
        actor_role=role.value,
        sprint_id=sprint_id,
        release_id=release_id,
        new_state=decision.value,
        reason=reason,
    )

    return DecisionRecord(
        release_id=release_id,
        decision=decision,
        actor=actor,
        role=role,
        reason=reason,
        timestamp=record.timestamp,
    )


def get_decision_status(session: Session, release_id: str) -> DecisionRecord | None:
    record = decision_repo.get_accepted_decision(session, release_id)
    if record is None:
        return None
    return DecisionRecord(
        release_id=record.release_id,
        decision=DecisionType(record.decision),
        actor=record.actor,
        role=Role(record.role),
        reason=record.reason,
        timestamp=record.timestamp,
    )
