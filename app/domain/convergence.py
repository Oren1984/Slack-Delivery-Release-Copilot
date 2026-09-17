from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.dataset import Defect, ScenarioDataset, WorkItem
from app.schemas.enums import (
    BusinessValue,
    DefectSeverity,
    DefectStatus,
    Priority,
    RiskLevel,
    WorkItemStatus,
)
from app.schemas.results import AtRiskItem, ConvergenceResult

# --- Deterministic weighting tables (documented in docs/CONVERGENCE_AND_DESCOPING.md) ---

STATUS_COMPLETION_RATIO: dict[WorkItemStatus, float] = {
    WorkItemStatus.DONE: 1.0,
    WorkItemStatus.IN_QA: 0.85,
    WorkItemStatus.IN_CODE_REVIEW: 0.6,
    WorkItemStatus.IN_PROGRESS: 0.35,
    WorkItemStatus.NOT_STARTED: 0.05,
    WorkItemStatus.BLOCKED: 0.0,
}

PRIORITY_WEIGHT: dict[Priority, float] = {
    Priority.CRITICAL: 4.0,
    Priority.HIGH: 3.0,
    Priority.MEDIUM: 2.0,
    Priority.LOW: 1.0,
}

VALUE_WEIGHT: dict[BusinessValue, float] = {
    BusinessValue.HIGH: 3.0,
    BusinessValue.MEDIUM: 2.0,
    BusinessValue.LOW: 1.0,
}

TIME_RISK_SAFETY_FACTOR = 0.8  # remaining effort must fit within 80% of hours left
TIME_RISK_PENALTY_MULTIPLIER = 0.5
DEPENDENCY_PENALTY_MULTIPLIER = 0.5
AT_RISK_THRESHOLD = 0.6
CARRYOVER_THRESHOLD = 0.5

RISK_LEVEL_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (80.0, RiskLevel.LOW),
    (60.0, RiskLevel.MEDIUM),
    (40.0, RiskLevel.HIGH),
    (0.0, RiskLevel.CRITICAL),
]

RECOMMENDED_ACTION: dict[RiskLevel, str] = {
    RiskLevel.LOW: "Proceed as planned; continue routine sprint monitoring.",
    RiskLevel.MEDIUM: "Monitor at-risk items closely and prepare contingency plans.",
    RiskLevel.HIGH: "Initiate a descoping review with the Delivery Manager and Tech Lead.",
    RiskLevel.CRITICAL: "Escalate immediately: convene stakeholders and review descoping "
    "candidates before sprint end.",
}


@dataclass
class _ItemAssessment:
    item: WorkItem
    completion_ratio: float
    reasons: list[str] = field(default_factory=list)


def hours_remaining_for(dataset: ScenarioDataset) -> float:
    delta = dataset.sprint.end_date - dataset.simulated_now
    return max(delta.total_seconds() / 3600.0, 0.0)


def open_blocking_defect_ids(defects: list[Defect]) -> set[str]:
    return {
        d.work_item_id
        for d in defects
        if d.work_item_id is not None
        and d.status == DefectStatus.OPEN
        and d.severity in (DefectSeverity.BLOCKER, DefectSeverity.CRITICAL)
    }


def assess_work_item(
    item: WorkItem, hours_remaining: float, blocking_defect_item_ids: set[str]
) -> _ItemAssessment:
    ratio = STATUS_COMPLETION_RATIO[item.status]
    reasons: list[str] = []

    if item.status == WorkItemStatus.BLOCKED:
        reasons.append("Work item status is Blocked.")

    if item.status != WorkItemStatus.DONE:
        if item.estimated_remaining_hours > hours_remaining * TIME_RISK_SAFETY_FACTOR:
            ratio *= TIME_RISK_PENALTY_MULTIPLIER
            reasons.append(
                f"Estimated remaining effort ({item.estimated_remaining_hours}h) exceeds "
                f"{TIME_RISK_SAFETY_FACTOR:.0%} of sprint time remaining ({hours_remaining:.1f}h)."
            )

        if item.blocking_dependency_ids:
            ratio *= DEPENDENCY_PENALTY_MULTIPLIER
            reasons.append(
                f"Blocked by unresolved dependencies: {', '.join(item.blocking_dependency_ids)}."
            )

        if item.id in blocking_defect_item_ids:
            ratio *= DEPENDENCY_PENALTY_MULTIPLIER
            reasons.append("Linked to an open Blocker/Critical defect.")

    return _ItemAssessment(item=item, completion_ratio=round(ratio, 4), reasons=reasons)


def classify_risk_level(score: float) -> RiskLevel:
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.CRITICAL


def analyze_convergence(dataset: ScenarioDataset) -> ConvergenceResult:
    """Deterministic sprint convergence analysis.

    For each committed work item, a completion ratio (0-1) is derived from
    its status and then penalized for time risk, unresolved dependencies,
    and open Blocker/Critical defects. The convergence score is the
    priority/business-value-weighted average of completion ratios across
    all committed items, scaled to 0-100. See
    docs/CONVERGENCE_AND_DESCOPING.md for the full rule reference.
    """
    hours_remaining = hours_remaining_for(dataset)
    blocking_defect_item_ids = open_blocking_defect_ids(dataset.defects)

    committed_items = [i for i in dataset.work_items if i.committed]
    assessments = [
        assess_work_item(item, hours_remaining, blocking_defect_item_ids)
        for item in committed_items
    ]

    weighted_sum = 0.0
    weight_total = 0.0
    for a in assessments:
        weight = PRIORITY_WEIGHT[a.item.priority] * VALUE_WEIGHT[a.item.business_value]
        weighted_sum += a.completion_ratio * weight
        weight_total += weight

    score = round((weighted_sum / weight_total) * 100, 1) if weight_total > 0 else 100.0
    risk_level = classify_risk_level(score)

    at_risk_items = [
        AtRiskItem(
            work_item_id=a.item.id,
            title=a.item.title,
            completion_ratio=a.completion_ratio,
            reasons=a.reasons,
        )
        for a in assessments
        if a.item.status != WorkItemStatus.DONE and a.completion_ratio < AT_RISK_THRESHOLD
    ]

    carryover_forecast = [
        a.item.id
        for a in assessments
        if a.item.status != WorkItemStatus.DONE and a.completion_ratio < CARRYOVER_THRESHOLD
    ]

    return ConvergenceResult(
        sprint_id=dataset.sprint.id,
        convergence_score=score,
        risk_level=risk_level,
        hours_remaining=round(hours_remaining, 1),
        at_risk_items=at_risk_items,
        carryover_forecast=carryover_forecast,
        recommended_action=RECOMMENDED_ACTION[risk_level],
    )
