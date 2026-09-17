from __future__ import annotations

import pytest

from app.core.errors import (
    DuplicateDecisionError,
    InvalidReleaseTransitionError,
    MissingEvidenceError,
    UnauthorizedDecisionError,
)
from app.domain.gate import evaluate_release_gate
from app.schemas.enums import DecisionType, GateStatus, Role
from app.services.approval_service import submit_decision
from tests.unit.factories import make_dataset, make_release_candidate, make_work_item


def _ready_dataset():
    return make_dataset(work_items=[make_work_item()])


def test_authorized_tech_lead_can_approve_ready_release(db_session):
    dataset = _ready_dataset()
    gate = evaluate_release_gate(dataset)
    record = submit_decision(
        db_session,
        dataset,
        gate,
        actor="Tessa Lead",
        role=Role.TECH_LEAD,
        decision=DecisionType.APPROVED,
        reason=None,
    )
    assert record.decision == DecisionType.APPROVED
    assert record.actor == "Tessa Lead"


def test_observer_cannot_approve(db_session):
    dataset = _ready_dataset()
    gate = evaluate_release_gate(dataset)
    with pytest.raises(UnauthorizedDecisionError):
        submit_decision(
            db_session,
            dataset,
            gate,
            actor="Olive Watcher",
            role=Role.OBSERVER,
            decision=DecisionType.APPROVED,
            reason=None,
        )


def test_role_self_assertion_is_rejected(db_session):
    dataset = _ready_dataset()
    gate = evaluate_release_gate(dataset)
    with pytest.raises(UnauthorizedDecisionError):
        submit_decision(
            db_session,
            dataset,
            gate,
            actor="Olive Watcher",
            role=Role.TECH_LEAD,
            decision=DecisionType.APPROVED,
            reason=None,
        )


def test_approval_rejected_when_gate_not_ready(db_session):
    item = make_work_item(qa_status="In Progress", required_for_sprint_goal=True)
    dataset = make_dataset(work_items=[item])
    gate = evaluate_release_gate(dataset)
    assert gate.gate_status == GateStatus.NOT_READY
    with pytest.raises(InvalidReleaseTransitionError):
        submit_decision(
            db_session,
            dataset,
            gate,
            actor="Tessa Lead",
            role=Role.TECH_LEAD,
            decision=DecisionType.APPROVED,
            reason=None,
        )


def test_approval_rejected_when_evidence_missing(db_session):
    dataset = make_dataset(
        work_items=[make_work_item()],
        release_candidate=make_release_candidate(rollback_plan_available=False),
    )
    gate = evaluate_release_gate(dataset)
    assert gate.gate_status == GateStatus.INSUFFICIENT_EVIDENCE
    with pytest.raises(MissingEvidenceError):
        submit_decision(
            db_session,
            dataset,
            gate,
            actor="Tessa Lead",
            role=Role.TECH_LEAD,
            decision=DecisionType.APPROVED,
            reason=None,
        )


def test_approval_rejected_when_no_gate_evaluation_on_record(db_session):
    dataset = _ready_dataset()
    with pytest.raises(InvalidReleaseTransitionError):
        submit_decision(
            db_session,
            dataset,
            None,
            actor="Tessa Lead",
            role=Role.TECH_LEAD,
            decision=DecisionType.APPROVED,
            reason=None,
        )


def test_hold_allowed_regardless_of_gate_status(db_session):
    item = make_work_item(qa_status="In Progress", required_for_sprint_goal=True)
    dataset = make_dataset(work_items=[item])
    gate = evaluate_release_gate(dataset)
    record = submit_decision(
        db_session,
        dataset,
        gate,
        actor="Quinn QA",
        role=Role.QA_LEAD,
        decision=DecisionType.HELD,
        reason="Needs more QA time.",
    )
    assert record.decision == DecisionType.HELD


def test_decision_cannot_be_silently_overwritten(db_session):
    dataset = _ready_dataset()
    gate = evaluate_release_gate(dataset)
    submit_decision(
        db_session,
        dataset,
        gate,
        actor="Tessa Lead",
        role=Role.TECH_LEAD,
        decision=DecisionType.APPROVED,
        reason=None,
    )
    with pytest.raises(DuplicateDecisionError):
        submit_decision(
            db_session,
            dataset,
            gate,
            actor="Quinn QA",
            role=Role.QA_LEAD,
            decision=DecisionType.HELD,
            reason="Trying to override.",
        )
