from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_dataset_adapter, get_session
from app.schemas.requests import CloseoutRequest
from app.schemas.results import CloseoutReport, RetrospectiveDraft
from app.services.closeout_service import generate_closeout_report
from app.services.retro_service import generate_retrospective_draft

router = APIRouter(prefix="/api/sprints", tags=["sprints"])


@router.post("/{sprint_id}/close-out", response_model=CloseoutReport)
def close_out_sprint(
    sprint_id: str,
    body: CloseoutRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> CloseoutReport:
    dataset = adapter.load(body.scenario_id)
    return generate_closeout_report(session, dataset)


@router.post("/{sprint_id}/retrospective", response_model=RetrospectiveDraft)
def retrospective_draft(
    sprint_id: str,
    body: CloseoutRequest,
    adapter=Depends(get_dataset_adapter),
    session: Session = Depends(get_session),
) -> RetrospectiveDraft:
    dataset = adapter.load(body.scenario_id)
    report = generate_closeout_report(session, dataset)
    return generate_retrospective_draft(session, dataset, report)
