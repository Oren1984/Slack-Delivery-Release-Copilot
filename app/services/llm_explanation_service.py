from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.llm.base import ExplanationKind, LLMAdapter, LLMUnavailableError
from app.adapters.llm.mock_llm import MockLLMAdapter
from app.adapters.llm.openai_compatible_llm import OpenAICompatibleLLMAdapter
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import llm_fallbacks_total
from app.repositories import audit_repo
from app.services import audit_events

logger = get_logger(__name__)

_mock_adapter = MockLLMAdapter()


def build_llm_adapter(settings: Settings | None = None) -> LLMAdapter:
    settings = settings or get_settings()
    if settings.llm_mode == "openai_compatible":
        try:
            return OpenAICompatibleLLMAdapter(
                base_url=settings.openai_compatible_base_url,
                api_key=settings.openai_compatible_api_key,
                model=settings.openai_compatible_model,
            )
        except LLMUnavailableError:
            logger.warning("openai_compatible adapter misconfigured; using mock adapter.")
            return _mock_adapter
    return _mock_adapter


def explain_with_fallback(
    session: Session,
    kind: ExplanationKind,
    context: dict,
    *,
    sprint_id: str | None = None,
    release_id: str | None = None,
    force_failure: bool = False,
) -> tuple[str, bool]:
    """Runs the configured LLM adapter and guarantees a usable result: on any
    failure or invalid output it falls back to the deterministic mock
    adapter, logs an llm_fallback_used audit event, and increments the
    fallback metric. The deterministic workflow result is never blocked or
    altered by this call.
    """
    adapter = build_llm_adapter()

    if force_failure:
        adapter = _RaisingAdapter()

    try:
        text = adapter.explain(kind, context)
        return text, False
    except LLMUnavailableError as exc:
        logger.warning(f"LLM adapter unavailable, falling back to mock: {exc}")
        llm_fallbacks_total.inc()
        audit_repo.append_event(
            session,
            event_type=audit_events.LLM_FALLBACK_USED,
            outcome="fallback",
            sprint_id=sprint_id,
            release_id=release_id,
            evidence_reference=kind,
        )
        return _mock_adapter.explain(kind, context), True


class _RaisingAdapter(LLMAdapter):
    def explain(self, kind: ExplanationKind, context: dict) -> str:
        raise LLMUnavailableError("Simulated LLM failure (force_llm_failure scenario flag).")
