from __future__ import annotations

from collections import Counter

from app.schemas.dataset import ScenarioDataset
from app.schemas.enums import FinalDisposition, WorkItemStatus


def calculate_say_do_ratio(dataset: ScenarioDataset) -> tuple[float, int, int]:
    """Say/Do Ratio = delivered committed items / committed planned items x 100.

    "Committed planned items" is every work item flagged committed=True,
    regardless of its final outcome. A descoped item is NOT removed from the
    denominator: it still counts as a commitment that was not delivered, so
    accepting an advisory descoping recommendation lowers the ratio exactly
    like any other non-delivery. This keeps the metric from being inflated
    by descoping. See docs/RELEASE_GATE_RULES.md / close-out docs.
    """
    committed = [i for i in dataset.work_items if i.committed]
    delivered = [i for i in committed if i.final_disposition == FinalDisposition.DELIVERED]
    planned_count = len(committed)
    delivered_count = len(delivered)
    ratio = round((delivered_count / planned_count) * 100, 1) if planned_count > 0 else 0.0
    return ratio, delivered_count, planned_count


def sprint_goal_protected(dataset: ScenarioDataset) -> bool:
    """True only if every work item required for the sprint goal was
    ultimately delivered."""
    goal_items = [i for i in dataset.work_items if i.required_for_sprint_goal]
    if not goal_items:
        return True
    return all(i.final_disposition == FinalDisposition.DELIVERED for i in goal_items)


def defect_summary(dataset: ScenarioDataset) -> dict[str, int]:
    summary: Counter[str] = Counter()
    for d in dataset.defects:
        key = f"{d.severity.value}_{d.status.value}".lower()
        summary[key] += 1
    return dict(summary)


def blocker_summary(dataset: ScenarioDataset) -> dict[str, int]:
    summary: Counter[str] = Counter()
    for item in dataset.work_items:
        if item.status == WorkItemStatus.BLOCKED or item.blocking_dependency_ids:
            summary["items_blocked"] += 1
    for defect in dataset.defects:
        if defect.blocker_category:
            summary[defect.blocker_category] += 1
    return dict(summary)


def repeated_blocker_categories(dataset: ScenarioDataset) -> list[str]:
    current = {d.blocker_category for d in dataset.defects if d.blocker_category}
    historical: set[str] = set()
    for hist in dataset.historical_sprints:
        historical.update(hist.blocker_categories)
    return sorted(current & historical)


def counts_by_disposition(dataset: ScenarioDataset) -> dict[FinalDisposition, int]:
    committed = [i for i in dataset.work_items if i.committed]
    counts: Counter[FinalDisposition] = Counter(i.final_disposition for i in committed)
    return dict(counts)
