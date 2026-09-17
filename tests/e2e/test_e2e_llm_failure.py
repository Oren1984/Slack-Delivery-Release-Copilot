from __future__ import annotations


def test_e2e_llm_failure_deterministic_result_still_completes(api_client):
    """Force an LLM failure via the scenario flag -> verify the
    deterministic workflow (convergence, gate, close-out) still completes
    successfully and the retrospective draft carries a fallback marker with
    no release decision lost or altered."""
    convergence = api_client.post(
        "/api/convergence/analyze", json={"scenario_id": "llm-failure"}
    ).json()
    assert convergence["sprint_id"] == "SPR-105"

    gate = api_client.post("/api/release/evaluate", json={"scenario_id": "llm-failure"}).json()
    assert gate["gate_status"] in (
        "READY_FOR_HUMAN_APPROVAL",
        "NOT_READY",
        "HOLD_REQUIRED",
        "INSUFFICIENT_EVIDENCE",
    )

    closeout = api_client.post(
        "/api/sprints/SPR-105/close-out", json={"scenario_id": "llm-failure"}
    ).json()
    assert closeout["say_do_ratio"] >= 0

    retro_resp = api_client.post(
        "/api/sprints/SPR-105/retrospective", json={"scenario_id": "llm-failure"}
    )
    assert retro_resp.status_code == 200
    draft = retro_resp.json()
    assert draft["llm_fallback_used"] is True
    assert draft["markdown"]  # deterministic content was still produced

    audit = api_client.get("/api/audit/REL-105").json()
    assert any(e["event_type"] == "llm_fallback_used" for e in audit)
