from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.metrics import gate_evaluations_total
from app.domain.gate import evaluate_release_gate
from app.repositories import audit_repo, gate_repo
from app.schemas.dataset import ScenarioDataset
from app.schemas.results import GateEvaluationResult
from app.services import audit_events


def run_gate_evaluation(session: Session, dataset: ScenarioDataset) -> GateEvaluationResult:
    result = evaluate_release_gate(dataset)
    gate_evaluations_total.inc()
    gate_repo.save_evaluation(session, result)
    audit_repo.append_event(
        session,
        event_type=audit_events.RELEASE_GATE_EVALUATED,
        outcome=result.gate_status.value,
        sprint_id=dataset.sprint.id,
        release_id=result.release_id,
        evidence_reference=dataset.scenario_id,
        new_state=result.gate_status.value,
    )
    return result


def get_latest_gate_result(session: Session, release_id: str) -> GateEvaluationResult | None:
    record = gate_repo.get_latest_evaluation(session, release_id)
    if record is None:
        return None
    return GateEvaluationResult.model_validate(record.payload_json)
