from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.dataset import ScenarioDataset
from app.schemas.enums import (
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    GateStatus,
    QAStatus,
)
from app.schemas.results import GateCheckResult, GateEvaluationResult

# Category precedence (highest wins): blocking_defect > hard_blocking > evidence.
# See docs/RELEASE_GATE_RULES.md for the full rule reference and effects.

NEXT_ACTION: dict[GateStatus, str] = {
    GateStatus.HOLD_REQUIRED: "Resolve all open Blocker/Critical defects before re-evaluating.",
    GateStatus.NOT_READY: "Complete outstanding QA, code review, testing, DoD, or dependency "
    "work before re-evaluating.",
    GateStatus.INSUFFICIENT_EVIDENCE: "Supply the missing release evidence (notes, rollback "
    "plan/owner, monitoring plan) before requesting human approval.",
    GateStatus.READY_FOR_HUMAN_APPROVAL: "Route the Release Readiness Card to an authorized "
    "approver (Tech Lead or QA Lead) for an Approve/Hold decision.",
}


def evaluate_release_gate(dataset: ScenarioDataset) -> GateEvaluationResult:
    """Deterministic release quality gate. Never returns "deployed" — the
    strongest possible outcome is READY_FOR_HUMAN_APPROVAL, which only
    signals that a human may now make the approval decision.
    """
    rc = dataset.release_candidate
    protected_items = [i for i in dataset.work_items if i.required_for_sprint_goal]
    committed_items = [i for i in dataset.work_items if i.committed]

    checks: list[GateCheckResult] = []

    open_blockers = [
        d
        for d in dataset.defects
        if d.status == DefectStatus.OPEN and d.severity == DefectSeverity.BLOCKER
    ]
    checks.append(
        GateCheckResult(
            name="no_open_blocker_defects",
            passed=not open_blockers,
            category="blocking_defect",
            detail=f"{len(open_blockers)} open Blocker defect(s)."
            if open_blockers
            else "No open Blocker defects.",
        )
    )

    open_critical = [
        d
        for d in dataset.defects
        if d.status == DefectStatus.OPEN and d.severity == DefectSeverity.CRITICAL
    ]
    checks.append(
        GateCheckResult(
            name="no_open_critical_defects",
            passed=not open_critical,
            category="blocking_defect",
            detail=f"{len(open_critical)} open Critical defect(s)."
            if open_critical
            else "No open Critical defects.",
        )
    )

    qa_incomplete = [i for i in protected_items if i.qa_status != QAStatus.PASSED]
    checks.append(
        GateCheckResult(
            name="release_critical_qa_complete",
            passed=not qa_incomplete,
            category="hard_blocking",
            detail=f"{len(qa_incomplete)} sprint-goal item(s) without passed QA."
            if qa_incomplete
            else "QA passed for all sprint-goal items.",
        )
    )

    dod_incomplete = [
        i
        for i in protected_items
        if not i.dod_checklist or any(not d.completed for d in i.dod_checklist)
    ]
    checks.append(
        GateCheckResult(
            name="dod_complete_for_protected_scope",
            passed=not dod_incomplete,
            category="hard_blocking",
            detail=f"{len(dod_incomplete)} sprint-goal item(s) with incomplete Definition of Done."
            if dod_incomplete
            else "Definition of Done complete for all sprint-goal items.",
        )
    )

    review_incomplete = [
        i for i in committed_items if i.code_review_status != CodeReviewStatus.APPROVED
    ]
    checks.append(
        GateCheckResult(
            name="required_code_reviews_complete",
            passed=not review_incomplete,
            category="hard_blocking",
            detail=f"{len(review_incomplete)} committed item(s) without an approved code review."
            if review_incomplete
            else "Code reviews approved for all committed items.",
        )
    )

    checks.append(
        GateCheckResult(
            name="required_tests_passed",
            passed=rc.tests_passed,
            category="hard_blocking",
            detail="Release candidate test suite passed."
            if rc.tests_passed
            else "Release candidate tests have not passed.",
        )
    )

    unresolved_deps = ", ".join(rc.unresolved_mandatory_dependencies)
    checks.append(
        GateCheckResult(
            name="no_unresolved_mandatory_dependency",
            passed=not rc.unresolved_mandatory_dependencies,
            category="hard_blocking",
            detail=f"Unresolved mandatory dependencies: {unresolved_deps}."
            if rc.unresolved_mandatory_dependencies
            else "No unresolved mandatory dependencies.",
        )
    )

    checks.append(
        GateCheckResult(
            name="release_notes_available",
            passed=rc.release_notes_available,
            category="evidence",
            detail="Release notes available."
            if rc.release_notes_available
            else "Release notes missing.",
        )
    )
    checks.append(
        GateCheckResult(
            name="rollback_plan_available",
            passed=rc.rollback_plan_available,
            category="evidence",
            detail="Rollback plan available."
            if rc.rollback_plan_available
            else "Rollback plan missing.",
        )
    )
    checks.append(
        GateCheckResult(
            name="rollback_owner_identified",
            passed=bool(rc.rollback_owner),
            category="evidence",
            detail=f"Rollback owner: {rc.rollback_owner}."
            if rc.rollback_owner
            else "No rollback owner identified.",
        )
    )
    checks.append(
        GateCheckResult(
            name="monitoring_plan_available",
            passed=rc.monitoring_plan_available,
            category="evidence",
            detail="Monitoring/validation plan available."
            if rc.monitoring_plan_available
            else "Monitoring/validation plan missing.",
        )
    )

    passed_checks = [c for c in checks if c.passed]
    failed_checks = [c for c in checks if not c.passed]
    blocking_defect_failures = [c for c in failed_checks if c.category == "blocking_defect"]
    hard_blocking_failures = [c for c in failed_checks if c.category == "hard_blocking"]
    evidence_failures = [c for c in failed_checks if c.category == "evidence"]

    if blocking_defect_failures:
        status = GateStatus.HOLD_REQUIRED
    elif hard_blocking_failures:
        status = GateStatus.NOT_READY
    elif evidence_failures:
        status = GateStatus.INSUFFICIENT_EVIDENCE
    else:
        status = GateStatus.READY_FOR_HUMAN_APPROVAL

    blocking_reasons = [c.detail for c in blocking_defect_failures + hard_blocking_failures]
    warnings = (
        [c.detail for c in evidence_failures] if status != GateStatus.INSUFFICIENT_EVIDENCE else []
    )
    if status == GateStatus.INSUFFICIENT_EVIDENCE:
        blocking_reasons = [c.detail for c in evidence_failures]

    return GateEvaluationResult(
        release_id=rc.id,
        gate_status=status,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        missing_evidence=evidence_failures,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
        recommended_next_action=NEXT_ACTION[status],
        evaluated_at=datetime.now(UTC),
    )
