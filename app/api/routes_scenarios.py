from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_dataset_adapter

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
def list_scenarios(adapter=Depends(get_dataset_adapter)) -> list[dict]:
    datasets = adapter.load_all()
    return [
        {
            "scenario_id": d.scenario_id,
            "title": d.title,
            "description": d.description,
            "sprint_id": d.sprint.id,
            "release_id": d.release_candidate.id,
        }
        for d in datasets
    ]


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str, adapter=Depends(get_dataset_adapter)) -> dict:
    dataset = adapter.load(scenario_id)
    return dataset.model_dump(mode="json")
