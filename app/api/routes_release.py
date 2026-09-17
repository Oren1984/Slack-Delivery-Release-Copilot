from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_dataset_adapter, get_session
from app.domain.convergence import analyze_convergence
from app.schemas.requests import EvaluateReleaseRequest, ReleaseDecisionRequest
from app.schemas.results import DecisionRecord, GateEvaluationResult, ReadinessCard
from app.services.approval_service import submit_decision
from app.services.gate_service import get_latest_gate_result, run_gate_evaluation
from app.services.readiness_card_service import build_readiness_card

router = APIRouter(prefix="/api", tags=["release"])


@router.post("/release/evaluate", response_model=GateEvaluationResult)
def evaluate_release(
    body: EvaluateReleaseRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> GateEvaluationResult:
    dataset = adapter.load(body.scenario_id)
    return run_gate_evaluation(session, dataset)


@router.get("/releases/{release_id}/readiness-card", response_model=ReadinessCard)
def get_readiness_card(
    release_id: str,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> ReadinessCard:
    dataset = adapter.find_by_release_id(release_id)
    gate = get_latest_gate_result(session, release_id)
    if gate is None:
        gate = run_gate_evaluation(session, dataset)
    convergence = analyze_convergence(dataset)
    return build_readiness_card(dataset, gate, convergence)


@router.post("/releases/{release_id}/decision", response_model=DecisionRecord)
def decide_release(
    release_id: str,
    body: ReleaseDecisionRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> DecisionRecord:
    dataset = adapter.load(body.scenario_id)
    gate = get_latest_gate_result(session, release_id)
    return submit_decision(
        session,
        dataset,
        gate,
        actor=body.actor,
        role=body.role,
        decision=body.decision,
        reason=body.reason,
    )
