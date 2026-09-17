from __future__ import annotations

from app.domain.convergence import (
    assess_work_item,
    hours_remaining_for,
    open_blocking_defect_ids,
)
from app.schemas.dataset import ScenarioDataset, WorkItem
from app.schemas.enums import (
    BusinessValue,
    DescopingRecommendation,
    Priority,
    RiskLevel,
    WorkItemStatus,
)
from app.schemas.results import ConvergenceResult, DescopingItemRecommendation, DescopingResult

DESCOPING_TIME_TRIGGER_HOURS = 48.0
DESCOPING_RISK_TRIGGER_LEVELS = (RiskLevel.HIGH, RiskLevel.CRITICAL)

LOW_PRIORITY_SET = (Priority.LOW, Priority.MEDIUM)
LOW_VALUE_SET = (BusinessValue.LOW, BusinessValue.MEDIUM)
EARLY_STAGE_SET = (WorkItemStatus.NOT_STARTED, WorkItemStatus.IN_PROGRESS)

IMPACT_TEXT: dict[DescopingRecommendation, str] = {
    DescopingRecommendation.PROTECT: "Removing this item would compromise the sprint goal.",
    DescopingRecommendation.CANDIDATE_FOR_DESCOPING: "Deferring this item preserves capacity "
    "for goal-critical work with limited impact on sprint objectives.",
    DescopingRecommendation.MUST_HOLD: "Item is incomplete and unsafe to release; it must not "
    "ship in its current state.",
    DescopingRecommendation.COMPLETED: "No action needed; work is already done.",
    DescopingRecommendation.NEEDS_HUMAN_REVIEW: "Rule coverage is insufficient to recommend a "
    "confident action; a human should assess this item directly.",
}


def _classify_item(
    item: WorkItem, completion_ratio: float, blocking_defect_item_ids: set[str]
) -> tuple[DescopingRecommendation, list[str], float]:
    reasons: list[str] = []

    if item.status == WorkItemStatus.DONE:
        return DescopingRecommendation.COMPLETED, ["Work item status is Done."], 1.0

    has_blocking_defect = item.id in blocking_defect_item_ids
    is_blocked_low_completion = (
        item.status == WorkItemStatus.BLOCKED or item.blocking_dependency_ids
    ) and completion_ratio < 0.5

    if item.required_for_sprint_goal and (has_blocking_defect or is_blocked_low_completion):
        if has_blocking_defect:
            reasons.append(
                "Required for sprint goal but linked to an open Blocker/Critical defect."
            )
        if is_blocked_low_completion:
            reasons.append("Required for sprint goal but blocked with low completion probability.")
        return DescopingRecommendation.MUST_HOLD, reasons, 0.9

    if item.required_for_sprint_goal:
        reasons.append("Marked as required for the sprint goal.")
        return DescopingRecommendation.PROTECT, reasons, 0.95

    is_low_priority = item.priority in LOW_PRIORITY_SET
    is_low_value = item.business_value in LOW_VALUE_SET
    is_early_stage = item.status in EARLY_STAGE_SET

    matched = sum([is_low_priority, is_low_value, is_early_stage])
    if is_low_priority and is_low_value and is_early_stage:
        reasons.append(f"Priority is {item.priority.value} (not sprint-critical).")
        reasons.append(f"Business value is {item.business_value.value}.")
        reasons.append(f"Work is still early-stage ({item.status.value}).")
        return DescopingRecommendation.CANDIDATE_FOR_DESCOPING, reasons, 0.6 + 0.1 * matched

    if is_blocked_low_completion:
        reasons.append("Blocked with low probability of completion and not required for the goal.")
        return DescopingRecommendation.CANDIDATE_FOR_DESCOPING, reasons, 0.55

    reasons.append(
        "No single deterministic rule matched confidently "
        f"(low_priority={is_low_priority}, low_value={is_low_value}, early_stage={is_early_stage})."
    )
    return DescopingRecommendation.NEEDS_HUMAN_REVIEW, reasons, 0.3 + 0.1 * matched


def generate_descoping_recommendations(
    dataset: ScenarioDataset, convergence: ConvergenceResult
) -> DescopingResult:
    """Advisory-only descoping recommendations. Never mutates work-item
    state; every recommendation requires an explicit human decision. See
    docs/CONVERGENCE_AND_DESCOPING.md for the full rule reference.
    """
    hours_remaining = hours_remaining_for(dataset)
    blocking_defect_item_ids = open_blocking_defect_ids(dataset.defects)

    trigger_reasons: list[str] = []
    if hours_remaining <= DESCOPING_TIME_TRIGGER_HOURS:
        trigger_reasons.append(
            f"Sprint ends within {DESCOPING_TIME_TRIGGER_HOURS:.0f} hours "
            f"({hours_remaining:.1f}h remaining)."
        )
    if convergence.risk_level in DESCOPING_RISK_TRIGGER_LEVELS:
        trigger_reasons.append(f"Convergence risk level is {convergence.risk_level.value}.")

    triggered = bool(trigger_reasons)

    recommendations: list[DescopingItemRecommendation] = []
    for item in dataset.work_items:
        assessment = assess_work_item(item, hours_remaining, blocking_defect_item_ids)
        recommendation, reasons, confidence = _classify_item(
            item, assessment.completion_ratio, blocking_defect_item_ids
        )
        recommendations.append(
            DescopingItemRecommendation(
                work_item_id=item.id,
                title=item.title,
                recommendation=recommendation,
                reasons=reasons,
                expected_impact=IMPACT_TEXT[recommendation],
                confidence=round(min(confidence, 1.0), 2),
                human_decision_required=recommendation != DescopingRecommendation.COMPLETED,
            )
        )

    return DescopingResult(
        sprint_id=dataset.sprint.id,
        triggered=triggered,
        trigger_reasons=trigger_reasons,
        recommendations=recommendations,
    )
