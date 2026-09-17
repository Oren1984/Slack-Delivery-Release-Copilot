from __future__ import annotations

from datetime import timedelta

from app.domain.convergence import analyze_convergence, classify_risk_level
from app.schemas.enums import Priority, RiskLevel, WorkItemStatus
from tests.unit.factories import SPRINT_END, make_dataset, make_work_item


def test_all_done_items_score_100_and_low_risk():
    dataset = make_dataset(work_items=[make_work_item(status=WorkItemStatus.DONE)])
    result = analyze_convergence(dataset)
    assert result.convergence_score == 100.0
    assert result.risk_level == RiskLevel.LOW
    assert result.at_risk_items == []
    assert result.carryover_forecast == []


def test_blocked_item_scores_zero_and_is_at_risk():
    dataset = make_dataset(
        work_items=[
            make_work_item(
                id="WI-BLOCKED",
                status=WorkItemStatus.BLOCKED,
                final_disposition="Pending",
            )
        ]
    )
    result = analyze_convergence(dataset)
    assert result.convergence_score == 0.0
    assert result.risk_level == RiskLevel.CRITICAL
    assert "WI-BLOCKED" in [i.work_item_id for i in result.at_risk_items]
    assert "WI-BLOCKED" in result.carryover_forecast


def test_time_risk_penalizes_items_that_cannot_fit_remaining_hours():
    at_risk_item = make_work_item(
        id="WI-TIME",
        status=WorkItemStatus.IN_PROGRESS,
        estimated_remaining_hours=1000,
        final_disposition="Pending",
    )
    dataset = make_dataset(
        work_items=[at_risk_item],
        simulated_now=SPRINT_END - timedelta(hours=10),
    )
    result = analyze_convergence(dataset)
    assert result.at_risk_items[0].work_item_id == "WI-TIME"
    assert any("exceeds" in r for r in result.at_risk_items[0].reasons)


def test_uncommitted_items_are_excluded_from_scoring():
    committed_done = make_work_item(id="WI-DONE", status=WorkItemStatus.DONE, committed=True)
    uncommitted_blocked = make_work_item(
        id="WI-UNCOMMITTED",
        status=WorkItemStatus.BLOCKED,
        committed=False,
        final_disposition="Pending",
    )
    dataset = make_dataset(work_items=[committed_done, uncommitted_blocked])
    result = analyze_convergence(dataset)
    assert result.convergence_score == 100.0


def test_priority_and_value_weighting_influences_score():
    low_weight_blocked = make_work_item(
        id="WI-LOW",
        status=WorkItemStatus.BLOCKED,
        priority=Priority.LOW,
        final_disposition="Pending",
    )
    high_weight_done = make_work_item(
        id="WI-HIGH", status=WorkItemStatus.DONE, priority=Priority.CRITICAL
    )
    dataset = make_dataset(work_items=[low_weight_blocked, high_weight_done])
    result = analyze_convergence(dataset)
    # The Critical-priority Done item dominates the weighted average.
    assert result.convergence_score > 50.0


def test_classify_risk_level_thresholds():
    assert classify_risk_level(85) == RiskLevel.LOW
    assert classify_risk_level(80) == RiskLevel.LOW
    assert classify_risk_level(79.9) == RiskLevel.MEDIUM
    assert classify_risk_level(60) == RiskLevel.MEDIUM
    assert classify_risk_level(59.9) == RiskLevel.HIGH
    assert classify_risk_level(40) == RiskLevel.HIGH
    assert classify_risk_level(39.9) == RiskLevel.CRITICAL
    assert classify_risk_level(0) == RiskLevel.CRITICAL
