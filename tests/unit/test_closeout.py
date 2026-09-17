from __future__ import annotations

from app.domain.closeout import (
    calculate_say_do_ratio,
    defect_summary,
    repeated_blocker_categories,
    sprint_goal_protected,
)
from app.schemas.dataset import Defect, HistoricalSprint
from app.schemas.enums import DefectSeverity, DefectStatus
from tests.unit.factories import make_dataset, make_work_item


def test_say_do_ratio_all_delivered_is_100():
    items = [make_work_item(id=f"WI-{i}", final_disposition="Delivered") for i in range(4)]
    dataset = make_dataset(work_items=items)
    ratio, delivered, planned = calculate_say_do_ratio(dataset)
    assert ratio == 100.0
    assert delivered == 4
    assert planned == 4


def test_say_do_ratio_penalizes_descoped_items():
    items = [
        make_work_item(id="WI-1", final_disposition="Delivered"),
        make_work_item(id="WI-2", final_disposition="Descoped"),
    ]
    dataset = make_dataset(work_items=items)
    ratio, delivered, planned = calculate_say_do_ratio(dataset)
    # Descoped item stays in the denominator: it counts against the ratio,
    # exactly like any other non-delivery.
    assert planned == 2
    assert delivered == 1
    assert ratio == 50.0


def test_say_do_ratio_ignores_uncommitted_items():
    items = [
        make_work_item(id="WI-1", final_disposition="Delivered", committed=True),
        make_work_item(id="WI-2", final_disposition="Pending", committed=False),
    ]
    dataset = make_dataset(work_items=items)
    ratio, delivered, planned = calculate_say_do_ratio(dataset)
    assert planned == 1
    assert ratio == 100.0


def test_say_do_ratio_zero_committed_items_is_zero_not_error():
    items = [make_work_item(id="WI-1", committed=False)]
    dataset = make_dataset(work_items=items)
    ratio, delivered, planned = calculate_say_do_ratio(dataset)
    assert ratio == 0.0
    assert planned == 0


def test_sprint_goal_protected_true_when_all_goal_items_delivered():
    items = [
        make_work_item(id="WI-1", required_for_sprint_goal=True, final_disposition="Delivered")
    ]
    dataset = make_dataset(work_items=items)
    assert sprint_goal_protected(dataset) is True


def test_sprint_goal_not_protected_when_goal_item_descoped():
    items = [make_work_item(id="WI-1", required_for_sprint_goal=True, final_disposition="Descoped")]
    dataset = make_dataset(work_items=items)
    assert sprint_goal_protected(dataset) is False


def test_defect_summary_groups_by_severity_and_status():
    dataset = make_dataset(
        defects=[
            Defect(id="DEF-1", severity=DefectSeverity.BLOCKER, status=DefectStatus.OPEN),
            Defect(id="DEF-2", severity=DefectSeverity.BLOCKER, status=DefectStatus.OPEN),
            Defect(id="DEF-3", severity=DefectSeverity.MINOR, status=DefectStatus.CLOSED),
        ]
    )
    summary = defect_summary(dataset)
    assert summary["blocker_open"] == 2
    assert summary["minor_closed"] == 1


def test_repeated_blocker_categories_intersects_current_and_historical():
    dataset = make_dataset(
        defects=[
            Defect(
                id="DEF-1",
                severity=DefectSeverity.MAJOR,
                status=DefectStatus.OPEN,
                blocker_category="flaky CI",
            )
        ],
        historical_sprints=[
            HistoricalSprint(
                sprint_name="Prior",
                say_do_ratio=80,
                blocker_categories=["flaky CI"],
                carryover_count=1,
            )
        ],
    )
    assert repeated_blocker_categories(dataset) == ["flaky CI"]


def test_no_repeated_blockers_when_categories_dont_overlap():
    dataset = make_dataset(
        defects=[
            Defect(
                id="DEF-1",
                severity=DefectSeverity.MAJOR,
                status=DefectStatus.OPEN,
                blocker_category="new issue",
            )
        ],
        historical_sprints=[
            HistoricalSprint(
                sprint_name="Prior",
                say_do_ratio=80,
                blocker_categories=["flaky CI"],
                carryover_count=1,
            )
        ],
    )
    assert repeated_blocker_categories(dataset) == []
