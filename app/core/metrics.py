from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest

registry = CollectorRegistry()

convergence_analyses_total = Counter(
    "convergence_analyses_total", "Convergence analyses completed", registry=registry
)
gate_evaluations_total = Counter(
    "gate_evaluations_total", "Release gate evaluations completed", registry=registry
)
release_approvals_total = Counter("release_approvals_total", "Releases approved", registry=registry)
release_holds_total = Counter("release_holds_total", "Releases held", registry=registry)
rejected_approval_attempts_total = Counter(
    "rejected_approval_attempts_total", "Rejected approval attempts", registry=registry
)
llm_fallbacks_total = Counter(
    "llm_fallbacks_total",
    "Times the LLM layer fell back to deterministic output",
    registry=registry,
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST
