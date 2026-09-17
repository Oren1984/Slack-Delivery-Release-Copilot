from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import DecisionType, Role


class AnalyzeConvergenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str


class EvaluateReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str


class ReleaseDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    actor: str
    role: Role
    decision: DecisionType
    reason: str | None = None


class CloseoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
