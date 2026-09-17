from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.descoping import generate_descoping_recommendations
from app.repositories import audit_repo
from app.schemas.dataset import ScenarioDataset
from app.schemas.results import ConvergenceResult, DescopingResult
from app.services import audit_events


def run_descoping_analysis(
    session: Session, dataset: ScenarioDataset, convergence: ConvergenceResult
) -> DescopingResult:
    result = generate_descoping_recommendations(dataset, convergence)
    audit_repo.append_event(
        session,
        event_type=audit_events.DESCOPING_RECOMMENDATION_GENERATED,
        outcome="completed" if result.triggered else "not_triggered",
        sprint_id=dataset.sprint.id,
        evidence_reference=dataset.scenario_id,
        new_state=f"{len(result.recommendations)} recommendations",
    )
    return result
