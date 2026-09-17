from __future__ import annotations

from datetime import datetime, timedelta

from app.schemas.dataset import (
    Actor,
    Defect,
    DodItem,
    ReleaseCandidate,
    ScenarioDataset,
    Sprint,
    WorkItem,
)
from app.schemas.enums import (
    BusinessValue,
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    FinalDisposition,
    Priority,
    QAStatus,
    Role,
    WorkItemStatus,
)

SPRINT_START = datetime.fromisoformat("2026-01-01T09:00:00+00:00")
SPRINT_END = datetime.fromisoformat("2026-01-12T18:00:00+00:00")


def make_work_item(**overrides) -> WorkItem:
    defaults = dict(
        id="WI-001",
        title="Sample work item",
        priority=Priority.MEDIUM,
        business_value=BusinessValue.MEDIUM,
        status=WorkItemStatus.DONE,
        code_review_status=CodeReviewStatus.APPROVED,
        qa_status=QAStatus.PASSED,
        dod_checklist=[],
        estimated_remaining_hours=0,
        blocking_dependency_ids=[],
        required_for_sprint_goal=False,
        committed=True,
        final_disposition=FinalDisposition.DELIVERED,
    )
    defaults.update(overrides)
    return WorkItem(**defaults)


def make_release_candidate(**overrides) -> ReleaseCandidate:
    defaults = dict(
        id="REL-TEST",
        version="v0.0.1",
        release_notes_available=True,
        rollback_plan_available=True,
        rollback_owner="Test Owner",
        monitoring_plan_available=True,
        tests_passed=True,
        unresolved_mandatory_dependencies=[],
    )
    defaults.update(overrides)
    return ReleaseCandidate(**defaults)


def make_dataset(
    *,
    work_items: list[WorkItem] | None = None,
    defects: list[Defect] | None = None,
    release_candidate: ReleaseCandidate | None = None,
    simulated_now: datetime | None = None,
    historical_sprints: list | None = None,
    force_llm_failure: bool = False,
    scenario_id: str = "unit-test-scenario",
) -> ScenarioDataset:
    return ScenarioDataset(
        scenario_id=scenario_id,
        title="Unit Test Scenario",
        description="Synthetic dataset built for unit testing.",
        sprint=Sprint(
            id="SPR-TEST",
            name="Unit Test Sprint",
            goal="Validate deterministic engine behavior.",
            start_date=SPRINT_START,
            end_date=SPRINT_END,
        ),
        work_items=work_items if work_items is not None else [make_work_item()],
        defects=defects or [],
        release_candidate=release_candidate or make_release_candidate(),
        authorized_actors=[
            Actor(name="Tessa Lead", role=Role.TECH_LEAD),
            Actor(name="Quinn QA", role=Role.QA_LEAD),
            Actor(name="Petra PMO", role=Role.DELIVERY_MANAGER),
            Actor(name="Olive Watcher", role=Role.OBSERVER),
        ],
        historical_sprints=historical_sprints or [],
        simulated_now=simulated_now or (SPRINT_END - timedelta(hours=72)),
        force_llm_failure=force_llm_failure,
    )


__all__ = [
    "DefectSeverity",
    "DefectStatus",
    "DodItem",
    "SPRINT_END",
    "SPRINT_START",
    "make_dataset",
    "make_release_candidate",
    "make_work_item",
]
