from __future__ import annotations

from app.domain.gate import evaluate_release_gate
from app.schemas.dataset import Defect
from app.schemas.enums import (
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    GateStatus,
    QAStatus,
)
from tests.unit.factories import make_dataset, make_release_candidate, make_work_item


def test_fully_compliant_release_is_ready_for_human_approval():
    dataset = make_dataset(work_items=[make_work_item()])
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.READY_FOR_HUMAN_APPROVAL
    assert result.blocking_reasons == []
    assert result.warnings == []


def test_open_blocker_defect_forces_hold_required():
    dataset = make_dataset(
        work_items=[make_work_item()],
        defects=[
            Defect(
                id="DEF-1",
                work_item_id="WI-001",
                severity=DefectSeverity.BLOCKER,
                status=DefectStatus.OPEN,
            )
        ],
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.HOLD_REQUIRED
    assert any("Blocker" in r for r in result.blocking_reasons)


def test_open_critical_defect_forces_hold_required():
    dataset = make_dataset(
        work_items=[make_work_item()],
        defects=[
            Defect(
                id="DEF-1",
                severity=DefectSeverity.CRITICAL,
                status=DefectStatus.OPEN,
            )
        ],
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.HOLD_REQUIRED


def test_closed_blocker_defect_does_not_block():
    dataset = make_dataset(
        work_items=[make_work_item()],
        defects=[Defect(id="DEF-1", severity=DefectSeverity.BLOCKER, status=DefectStatus.CLOSED)],
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.READY_FOR_HUMAN_APPROVAL


def test_incomplete_dod_on_protected_scope_is_not_ready():
    item = make_work_item(
        required_for_sprint_goal=True,
        dod_checklist=[{"description": "must finish", "completed": False}],
    )
    dataset = make_dataset(work_items=[item])
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.NOT_READY
    assert any("Definition of Done" in c.detail for c in result.failed_checks)


def test_qa_not_passed_on_protected_scope_is_not_ready():
    item = make_work_item(required_for_sprint_goal=True, qa_status=QAStatus.IN_PROGRESS)
    dataset = make_dataset(work_items=[item])
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.NOT_READY


def test_missing_code_review_is_not_ready():
    item = make_work_item(code_review_status=CodeReviewStatus.IN_REVIEW)
    dataset = make_dataset(work_items=[item])
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.NOT_READY


def test_missing_rollback_plan_is_insufficient_evidence():
    dataset = make_dataset(
        work_items=[make_work_item()],
        release_candidate=make_release_candidate(rollback_plan_available=False),
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.INSUFFICIENT_EVIDENCE
    assert any("Rollback plan" in r for r in result.blocking_reasons)


def test_missing_rollback_owner_is_insufficient_evidence():
    dataset = make_dataset(
        work_items=[make_work_item()],
        release_candidate=make_release_candidate(rollback_owner=None),
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.INSUFFICIENT_EVIDENCE


def test_blocking_defect_takes_precedence_over_missing_evidence():
    dataset = make_dataset(
        work_items=[make_work_item()],
        defects=[Defect(id="DEF-1", severity=DefectSeverity.BLOCKER, status=DefectStatus.OPEN)],
        release_candidate=make_release_candidate(rollback_plan_available=False),
    )
    result = evaluate_release_gate(dataset)
    assert result.gate_status == GateStatus.HOLD_REQUIRED


def test_gate_never_returns_deployed():
    for status in GateStatus:
        assert status.value != "DEPLOYED"
