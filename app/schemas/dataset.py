from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import (
    BusinessValue,
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    FinalDisposition,
    Priority,
    QAStatus,
    Role,
    WorkItemStatus,
)


class DodItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    completed: bool


class WorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    priority: Priority
    business_value: BusinessValue
    status: WorkItemStatus
    code_review_status: CodeReviewStatus
    qa_status: QAStatus
    dod_checklist: list[DodItem] = Field(default_factory=list)
    estimated_remaining_hours: float = Field(ge=0)
    blocking_dependency_ids: list[str] = Field(default_factory=list)
    required_for_sprint_goal: bool = False
    committed: bool = True
    final_disposition: FinalDisposition = FinalDisposition.PENDING


class Defect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    work_item_id: str | None = None
    severity: DefectSeverity
    status: DefectStatus
    blocker_category: str | None = None
    description: str = ""


class ReleaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    release_notes_available: bool
    rollback_plan_available: bool
    rollback_owner: str | None = None
    monitoring_plan_available: bool
    tests_passed: bool
    unresolved_mandatory_dependencies: list[str] = Field(default_factory=list)


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: Role


class HistoricalSprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_name: str
    say_do_ratio: float
    blocker_categories: list[str] = Field(default_factory=list)
    carryover_count: int = 0


class Sprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    goal: str
    start_date: datetime
    end_date: datetime


class ScenarioDataset(BaseModel):
    """Root schema for a synthetic scenario file. Validated on load; a
    malformed or incomplete file produces a controlled ValidationFailedError
    rather than an unhandled exception.
    """

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    title: str
    description: str
    sprint: Sprint
    work_items: list[WorkItem]
    defects: list[Defect] = Field(default_factory=list)
    release_candidate: ReleaseCandidate
    authorized_actors: list[Actor]
    historical_sprints: list[HistoricalSprint] = Field(default_factory=list)
    simulated_now: datetime
    force_llm_failure: bool = False

    @model_validator(mode="after")
    def _check_references(self) -> ScenarioDataset:
        item_ids = {i.id for i in self.work_items}
        for defect in self.defects:
            if defect.work_item_id is not None and defect.work_item_id not in item_ids:
                raise ValueError(
                    f"defect {defect.id} references unknown work_item_id {defect.work_item_id}"
                )
        for item in self.work_items:
            for dep_id in item.blocking_dependency_ids:
                if dep_id not in item_ids:
                    raise ValueError(f"work item {item.id} references unknown dependency {dep_id}")
        return self
