from __future__ import annotations

from app.adapters.slack_adapter import build_readiness_card_block_kit
from app.domain.closeout import defect_summary
from app.schemas.dataset import ScenarioDataset
from app.schemas.enums import QAStatus, WorkItemStatus
from app.schemas.results import ConvergenceResult, GateEvaluationResult, ReadinessCard


def build_readiness_card(
    dataset: ScenarioDataset,
    gate: GateEvaluationResult,
    convergence: ConvergenceResult,
) -> ReadinessCard:
    completed = sum(1 for i in dataset.work_items if i.status == WorkItemStatus.DONE)
    planned = len(dataset.work_items)

    protected = [i for i in dataset.work_items if i.required_for_sprint_goal]
    qa_passed = sum(1 for i in protected if i.qa_status == QAStatus.PASSED)
    qa_summary = f"{qa_passed}/{len(protected)} sprint-goal items QA passed" if protected else "N/A"

    dod_complete = sum(
        1 for i in protected if i.dod_checklist and all(d.completed for d in i.dod_checklist)
    )
    dod_summary = (
        f"{dod_complete}/{len(protected)} sprint-goal items DoD complete" if protected else "N/A"
    )

    rollback_ready = dataset.release_candidate.rollback_plan_available and bool(
        dataset.release_candidate.rollback_owner
    )

    audit_reference = f"release:{dataset.release_candidate.id}"

    block_kit = build_readiness_card_block_kit(
        release_id=dataset.release_candidate.id,
        version=dataset.release_candidate.version,
        sprint_name=dataset.sprint.name,
        gate=gate,
        convergence_score=convergence.convergence_score,
        completed_count=completed,
        planned_count=planned,
        open_defect_summary=defect_summary(dataset),
        qa_summary=qa_summary,
        dod_summary=dod_summary,
        rollback_ready=rollback_ready,
        audit_reference=audit_reference,
    )

    return ReadinessCard(
        release_id=dataset.release_candidate.id,
        version=dataset.release_candidate.version,
        sprint_name=dataset.sprint.name,
        gate_status=gate.gate_status,
        convergence_score=convergence.convergence_score,
        completed_count=completed,
        planned_count=planned,
        open_defect_summary=defect_summary(dataset),
        qa_summary=qa_summary,
        dod_summary=dod_summary,
        rollback_ready=rollback_ready,
        main_blockers=gate.blocking_reasons,
        recommended_action=gate.recommended_next_action,
        audit_reference=audit_reference,
        block_kit=block_kit,
    )
