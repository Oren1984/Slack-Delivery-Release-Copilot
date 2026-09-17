from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_dataset_adapter, get_session
from app.repositories import audit_repo
from app.schemas.requests import AnalyzeConvergenceRequest
from app.schemas.results import ConvergenceResult, DescopingResult
from app.services import audit_events
from app.services.convergence_service import run_convergence_analysis
from app.services.descoping_service import run_descoping_analysis

router = APIRouter(prefix="/api/convergence", tags=["convergence"])


@router.post("/analyze", response_model=ConvergenceResult)
def analyze_convergence(
    body: AnalyzeConvergenceRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> ConvergenceResult:
    dataset = adapter.load(body.scenario_id)
    audit_repo.append_event(
        session,
        event_type=audit_events.DATASET_LOADED,
        outcome="loaded",
        sprint_id=dataset.sprint.id,
        release_id=dataset.release_candidate.id,
        evidence_reference=dataset.scenario_id,
    )
    return run_convergence_analysis(session, dataset)


@router.post("/descope", response_model=DescopingResult)
def analyze_descoping(
    body: AnalyzeConvergenceRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> DescopingResult:
    dataset = adapter.load(body.scenario_id)
    convergence = run_convergence_analysis(session, dataset)
    return run_descoping_analysis(session, dataset, convergence)
