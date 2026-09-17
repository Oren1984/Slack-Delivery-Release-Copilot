from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.metrics import convergence_analyses_total
from app.domain.convergence import analyze_convergence
from app.repositories import audit_repo
from app.schemas.dataset import ScenarioDataset
from app.schemas.results import ConvergenceResult
from app.services import audit_events


def run_convergence_analysis(session: Session, dataset: ScenarioDataset) -> ConvergenceResult:
    result = analyze_convergence(dataset)
    convergence_analyses_total.inc()
    audit_repo.append_event(
        session,
        event_type=audit_events.CONVERGENCE_ANALYSIS_COMPLETED,
        outcome="completed",
        sprint_id=dataset.sprint.id,
        evidence_reference=dataset.scenario_id,
        new_state=result.risk_level.value,
    )
    return result
