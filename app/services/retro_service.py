from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.dataset import ScenarioDataset
from app.schemas.results import CloseoutReport, RetrospectiveDraft
from app.services.llm_explanation_service import explain_with_fallback


def _build_markdown(dataset: ScenarioDataset, report: CloseoutReport, intro: str) -> str:
    went_well = []
    if report.say_do_ratio >= 90:
        went_well.append(f"Strong delivery predictability: Say/Do Ratio of {report.say_do_ratio}%.")
    if report.sprint_goal_protected:
        went_well.append("The sprint goal was fully protected and delivered.")
    if not report.repeated_blocker_categories:
        went_well.append("No blocker categories repeated from prior sprints.")
    if not went_well:
        went_well.append("Team maintained visibility into risk throughout the sprint.")

    went_wrong = []
    if report.say_do_ratio < 90:
        went_wrong.append(f"Say/Do Ratio was {report.say_do_ratio}%, below the 90% target.")
    if report.carryover_count > 0:
        went_wrong.append(f"{report.carryover_count} committed item(s) carried over.")
    if report.descoped_count > 0:
        went_wrong.append(
            f"{report.descoped_count} item(s) were descoped from the original commitment."
        )
    if not report.sprint_goal_protected:
        went_wrong.append("The sprint goal was not fully protected.")
    if not went_wrong:
        went_wrong.append("No significant delivery issues identified.")

    questions = [
        "Are current estimation practices accounting for dependency and QA risk accurately?",
        "Should the descoping trigger threshold change for the next sprint?",
    ]
    repeated_blockers_text = ", ".join(report.repeated_blocker_categories)
    if report.repeated_blocker_categories:
        questions.append(
            f"Why do these blocker categories keep recurring: {repeated_blockers_text}?"
        )

    md = f"""# Retrospective Draft — {dataset.sprint.name}

{intro}

## What Went Well
{chr(10).join(f"- {w}" for w in went_well)}

## What Did Not Go Well
{chr(10).join(f"- {w}" for w in went_wrong)}

## Repeated Blockers
{repeated_blockers_text or "None identified."}

## Quality Observations
- Defect summary: {report.defect_summary or "No defects recorded."}

## Release Process Observations
- Release decision: {report.release_decision or "Not yet decided"}
- Approved/held by: {report.approval_actor or "N/A"}

## Suggested Improvement Actions
{chr(10).join(f"- {a} (Owner: TBD)" for a in report.recommended_actions_next_sprint)}

## Open Questions for the Team
{chr(10).join(f"- {q}" for q in questions)}
"""
    return md


def generate_retrospective_draft(
    session: Session, dataset: ScenarioDataset, report: CloseoutReport
) -> RetrospectiveDraft:
    """Deterministic engine supplies every fact; the LLM layer (mock by
    default) may only smooth the introductory wording. Failure of the LLM
    layer never blocks the draft — see explain_with_fallback.
    """
    intro, used_fallback = explain_with_fallback(
        session,
        "retrospective_draft",
        {
            "sprint_id": dataset.sprint.id,
            "say_do_ratio": report.say_do_ratio,
        },
        sprint_id=dataset.sprint.id,
        release_id=dataset.release_candidate.id,
        force_failure=dataset.force_llm_failure,
    )

    markdown = _build_markdown(dataset, report, intro)
    slack_text = (
        f"*Retrospective — {dataset.sprint.name}*\n{intro}\n"
        f"Say/Do Ratio: {report.say_do_ratio}% | Carryover: {report.carryover_count} | "
        f"Descoped: {report.descoped_count}"
    )

    return RetrospectiveDraft(
        sprint_id=dataset.sprint.id,
        markdown=markdown,
        slack_text=slack_text,
        llm_enhanced=True,
        llm_fallback_used=used_fallback,
    )
