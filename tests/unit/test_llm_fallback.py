from __future__ import annotations

from app.repositories import audit_repo
from app.services.llm_explanation_service import explain_with_fallback


def test_mock_adapter_returns_text_without_fallback(db_session):
    text, used_fallback = explain_with_fallback(
        db_session,
        "executive_summary",
        {"version": "v1.0.0", "gate_status": "READY_FOR_HUMAN_APPROVAL"},
    )
    assert used_fallback is False
    assert "v1.0.0" in text


def test_forced_failure_falls_back_to_deterministic_output(db_session):
    text, used_fallback = explain_with_fallback(
        db_session,
        "executive_summary",
        {"version": "v1.0.0", "gate_status": "READY_FOR_HUMAN_APPROVAL"},
        force_failure=True,
    )
    assert used_fallback is True
    assert "v1.0.0" in text  # deterministic mock still produced a valid result


def test_forced_failure_records_audit_event(db_session):
    explain_with_fallback(
        db_session,
        "blocker_summary",
        {"blocking_reasons": ["Open blocker defect"]},
        sprint_id="SPR-TEST",
        release_id="REL-TEST",
        force_failure=True,
    )
    events = audit_repo.list_events(db_session, release_id="REL-TEST")
    assert any(e.event_type == "llm_fallback_used" for e in events)


def test_llm_failure_never_raises_to_caller(db_session):
    # explain_with_fallback must never propagate LLMUnavailableError.
    text, used_fallback = explain_with_fallback(
        db_session, "descoping_explanation", {"recommendations": []}, force_failure=True
    )
    assert isinstance(text, str)
    assert text != ""
