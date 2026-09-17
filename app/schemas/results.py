from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import (
    DecisionType,
    DescopingRecommendation,
    GateStatus,
    RiskLevel,
    Role,
)


class AtRiskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item_id: str
    title: str
    completion_ratio: float
    reasons: list[str]


class ConvergenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_id: str
    convergence_score: float
    risk_level: RiskLevel
    hours_remaining: float
    at_risk_items: list[AtRiskItem]
    carryover_forecast: list[str]
    recommended_action: str


class DescopingItemRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item_id: str
    title: str
    recommendation: DescopingRecommendation
    reasons: list[str]
    expected_impact: str
    confidence: float
    human_decision_required: bool = True


class DescopingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_id: str
    triggered: bool
    trigger_reasons: list[str]
    recommendations: list[DescopingItemRecommendation]


class GateCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    category: str  # "blocking_defect" | "hard_blocking" | "evidence"
    detail: str


class GateEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_id: str
    gate_status: GateStatus
    passed_checks: list[GateCheckResult]
    failed_checks: list[GateCheckResult]
    missing_evidence: list[GateCheckResult]
    blocking_reasons: list[str]
    warnings: list[str]
    recommended_next_action: str
    evaluated_at: datetime


class ReadinessCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_id: str
    version: str
    sprint_name: str
    gate_status: GateStatus
    convergence_score: float
    completed_count: int
    planned_count: int
    open_defect_summary: dict[str, int]
    qa_summary: str
    dod_summary: str
    rollback_ready: bool
    main_blockers: list[str]
    recommended_action: str
    audit_reference: str
    block_kit: dict


class DecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_id: str
    decision: DecisionType
    actor: str
    role: Role
    reason: str | None
    timestamp: datetime


class CloseoutReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_id: str
    planned_count: int
    delivered_count: int
    descoped_count: int
    carryover_count: int
    say_do_ratio: float
    sprint_goal_protected: bool
    defect_summary: dict[str, int]
    blocker_summary: dict[str, int]
    release_decision: str | None
    approval_actor: str | None
    approval_timestamp: datetime | None
    repeated_blocker_categories: list[str]
    operational_lessons: list[str]
    recommended_actions_next_sprint: list[str]


class RetrospectiveDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sprint_id: str
    markdown: str
    slack_text: str
    llm_enhanced: bool
    llm_fallback_used: bool


class AuditEventOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    event_type: str
    timestamp: datetime
    actor: str | None
    actor_role: str | None
    sprint_id: str | None
    release_id: str | None
    evidence_reference: str | None
    previous_state: str | None
    new_state: str | None
    reason: str | None
    outcome: str
    correlation_id: str
