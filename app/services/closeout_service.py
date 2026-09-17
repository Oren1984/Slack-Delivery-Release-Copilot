from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.closeout import (
    blocker_summary,
    calculate_say_do_ratio,
    counts_by_disposition,
    defect_summary,
    repeated_blocker_categories,
    sprint_goal_protected,
)
from app.repositories import audit_repo, closeout_repo, decision_repo
from app.schemas.dataset import ScenarioDataset
from app.schemas.enums import FinalDisposition
from app.schemas.results import CloseoutReport
from app.services import audit_events

LESSON_RULES: list[tuple[str, str]] = [
    ("say_do_below_70", "Say/Do Ratio fell below 70%: review sprint commitment sizing."),
    (
        "goal_not_protected",
        "The sprint goal was not fully protected: revisit prioritization "
        "and descoping timing in planning.",
    ),
    (
        "carryover_present",
        "Committed items carried over: assess whether estimation or "
        "capacity planning needs adjustment.",
    ),
    (
        "repeated_blockers",
        "One or more blocker categories recurred from prior sprints: "
        "treat as a standing risk in the next planning session.",
    ),
]


def generate_closeout_report(session: Session, dataset: ScenarioDataset) -> CloseoutReport:
    ratio, delivered_count, planned_count = calculate_say_do_ratio(dataset)
    disposition_counts = counts_by_disposition(dataset)
    descoped_count = disposition_counts.get(FinalDisposition.DESCOPED, 0)
    carryover_count = disposition_counts.get(
        FinalDisposition.CARRIED_OVER, 0
    ) + disposition_counts.get(FinalDisposition.PENDING, 0)
    goal_protected = sprint_goal_protected(dataset)
    repeated = repeated_blocker_categories(dataset)

    release_id = dataset.release_candidate.id
    decision_record = decision_repo.get_accepted_decision(session, release_id)
    release_decision = decision_record.decision if decision_record else None  # already a str
    approval_actor = decision_record.actor if decision_record else None
    approval_timestamp = decision_record.timestamp if decision_record else None

    lessons: list[str] = []
    if ratio < 70:
        lessons.append(dict(LESSON_RULES)["say_do_below_70"])
    if not goal_protected:
        lessons.append(dict(LESSON_RULES)["goal_not_protected"])
    if carryover_count > 0:
        lessons.append(dict(LESSON_RULES)["carryover_present"])
    if repeated:
        lessons.append(dict(LESSON_RULES)["repeated_blockers"])
    if not lessons:
        lessons.append("No systemic issues detected; sprint executed to plan.")

    candidate_actions: list[str | None] = [
        f"Address recurring blocker categories: {', '.join(repeated)}." if repeated else None,
        "Revisit estimation accuracy for carried-over items." if carryover_count > 0 else None,
        "Maintain current sprint commitment approach." if ratio >= 90 and not repeated else None,
    ]
    recommended_actions: list[str] = [a for a in candidate_actions if a]
    if not recommended_actions:
        recommended_actions.append("Continue current practices into the next sprint.")

    report = CloseoutReport(
        sprint_id=dataset.sprint.id,
        planned_count=planned_count,
        delivered_count=delivered_count,
        descoped_count=descoped_count,
        carryover_count=carryover_count,
        say_do_ratio=ratio,
        sprint_goal_protected=goal_protected,
        defect_summary=defect_summary(dataset),
        blocker_summary=blocker_summary(dataset),
        release_decision=release_decision,
        approval_actor=approval_actor,
        approval_timestamp=approval_timestamp,
        repeated_blocker_categories=repeated,
        operational_lessons=lessons,
        recommended_actions_next_sprint=recommended_actions,
    )

    closeout_repo.save_report(session, dataset.sprint.id, report)
    audit_repo.append_event(
        session,
        event_type=audit_events.CLOSEOUT_GENERATED,
        outcome="completed",
        sprint_id=dataset.sprint.id,
        release_id=release_id,
        evidence_reference=dataset.scenario_id,
        new_state=f"say_do={ratio}",
    )
    return report
