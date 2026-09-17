from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import (
    ReleaseNotFoundError,
    ScenarioNotFoundError,
    SprintNotFoundError,
    ValidationFailedError,
)
from app.schemas.dataset import ScenarioDataset


class LocalDatasetAdapter:
    """Offline adapter that loads synthetic scenario datasets from local
    JSON files. This is the only supported dataset source for the POC; no
    network or external PM-tool integration is performed.
    """

    def __init__(self, scenarios_dir: str | Path | None = None) -> None:
        self._dir = Path(scenarios_dir or get_settings().scenarios_dir)

    def list_scenario_files(self) -> list[Path]:
        if not self._dir.exists():
            return []
        return sorted(self._dir.glob("*.json"))

    def load_all(self) -> list[ScenarioDataset]:
        return [self._load_file(path) for path in self.list_scenario_files()]

    def load(self, scenario_id: str) -> ScenarioDataset:
        for path in self.list_scenario_files():
            dataset = self._load_file(path)
            if dataset.scenario_id == scenario_id:
                return dataset
        raise ScenarioNotFoundError(f"Scenario '{scenario_id}' was not found.")

    def find_by_release_id(self, release_id: str) -> ScenarioDataset:
        for dataset in self.load_all():
            if dataset.release_candidate.id == release_id:
                return dataset
        raise ReleaseNotFoundError(f"Release '{release_id}' was not found in any scenario.")

    def find_by_sprint_id(self, sprint_id: str) -> ScenarioDataset:
        for dataset in self.load_all():
            if dataset.sprint.id == sprint_id:
                return dataset
        raise SprintNotFoundError(f"Sprint '{sprint_id}' was not found in any scenario.")

    def _load_file(self, path: Path) -> ScenarioDataset:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationFailedError(
                f"Scenario file '{path.name}' is not valid JSON: {exc}"
            ) from exc
        try:
            return ScenarioDataset.model_validate(raw)
        except ValidationError as exc:
            raise ValidationFailedError(
                f"Scenario file '{path.name}' failed schema validation: "
                f"{exc.error_count()} error(s)."
            ) from exc
