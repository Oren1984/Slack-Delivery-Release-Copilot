from __future__ import annotations

from datetime import timedelta

from app.domain.convergence import analyze_convergence
from app.domain.descoping import generate_descoping_recommendations
from app.schemas.enums import (
    BusinessValue,
    DefectSeverity,
    DefectStatus,
    DescopingRecommendation,
    Priority,
    WorkItemStatus,
)
from tests.unit.factories import SPRINT_END, make_dataset, make_work_item


def _recommend(dataset):
    convergence = analyze_convergence(dataset)
    return generate_descoping_recommendations(dataset, convergence)


def test_done_item_is_classified_completed():
    dataset = make_dataset(work_items=[make_work_item(status=WorkItemStatus.DONE)])
    result = _recommend(dataset)
    assert result.recommendations[0].recommendation == DescopingRecommendation.COMPLETED


def test_required_for_goal_item_is_protected():
    item = make_work_item(
        status=WorkItemStatus.IN_PROGRESS,
        required_for_sprint_goal=True,
        final_disposition="Pending",
    )
    dataset = make_dataset(work_items=[item])
    result = _recommend(dataset)
    assert result.recommendations[0].recommendation == DescopingRecommendation.PROTECT


def test_required_for_goal_item_with_blocking_defect_is_must_hold():
    item = make_work_item(
        id="WI-GOAL",
        status=WorkItemStatus.IN_PROGRESS,
        required_for_sprint_goal=True,
        final_disposition="Pending",
    )
    defect = {
        "id": "DEF-1",
        "work_item_id": "WI-GOAL",
        "severity": DefectSeverity.BLOCKER,
        "status": DefectStatus.OPEN,
    }
    from app.schemas.dataset import Defect

    dataset = make_dataset(work_items=[item], defects=[Defect(**defect)])
    result = _recommend(dataset)
    assert result.recommendations[0].recommendation == DescopingRecommendation.MUST_HOLD


def test_low_priority_low_value_early_stage_item_is_candidate_for_descoping():
    item = make_work_item(
        status=WorkItemStatus.NOT_STARTED,
        priority=Priority.LOW,
        business_value=BusinessValue.LOW,
        required_for_sprint_goal=False,
        final_disposition="Pending",
    )
    dataset = make_dataset(work_items=[item])
    result = _recommend(dataset)
    assert (
        result.recommendations[0].recommendation == DescopingRecommendation.CANDIDATE_FOR_DESCOPING
    )
    assert result.recommendations[0].human_decision_required is True


def test_ambiguous_item_needs_human_review():
    item = make_work_item(
        status=WorkItemStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        business_value=BusinessValue.LOW,
        required_for_sprint_goal=False,
        final_disposition="Pending",
    )
    dataset = make_dataset(work_items=[item])
    result = _recommend(dataset)
    assert result.recommendations[0].recommendation == DescopingRecommendation.NEEDS_HUMAN_REVIEW


def test_engine_never_mutates_work_item_state():
    item = make_work_item(
        status=WorkItemStatus.NOT_STARTED,
        priority=Priority.LOW,
        business_value=BusinessValue.LOW,
        final_disposition="Pending",
    )
    dataset = make_dataset(work_items=[item])
    original_status = item.status
    _recommend(dataset)
    assert dataset.work_items[0].status == original_status


def test_trigger_fires_within_48_hours():
    dataset = make_dataset(
        work_items=[make_work_item(status=WorkItemStatus.DONE)],
        simulated_now=SPRINT_END - timedelta(hours=10),
    )
    result = _recommend(dataset)
    assert result.triggered is True
    assert any("48" in r for r in result.trigger_reasons)


def test_trigger_does_not_fire_when_far_from_deadline_and_low_risk():
    dataset = make_dataset(
        work_items=[make_work_item(status=WorkItemStatus.DONE)],
        simulated_now=SPRINT_END - timedelta(hours=200),
    )
    result = _recommend(dataset)
    assert result.triggered is False
