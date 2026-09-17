from __future__ import annotations


def test_e2e_healthy_release_full_workflow(api_client):
    """Load scenario -> analyze convergence -> evaluate gate -> approve ->
    generate close-out -> verify audit trail."""
    scenario = api_client.get("/api/scenarios/healthy-release").json()
    assert scenario["sprint"]["id"] == "SPR-101"

    convergence = api_client.post(
        "/api/convergence/analyze", json={"scenario_id": "healthy-release"}
    ).json()
    assert convergence["risk_level"] == "Low"

    gate = api_client.post("/api/release/evaluate", json={"scenario_id": "healthy-release"}).json()
    assert gate["gate_status"] == "READY_FOR_HUMAN_APPROVAL"

    decision_resp = api_client.post(
        "/api/releases/REL-101/decision",
        json={
            "scenario_id": "healthy-release",
            "actor": "Elena Cho",
            "role": "Tech Lead",
            "decision": "APPROVED",
        },
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["decision"] == "APPROVED"

    closeout = api_client.post(
        "/api/sprints/SPR-101/close-out", json={"scenario_id": "healthy-release"}
    ).json()
    assert closeout["release_decision"] == "APPROVED"
    assert closeout["approval_actor"] == "Elena Cho"

    audit = api_client.get("/api/audit/REL-101").json()
    event_types = {e["event_type"] for e in audit}
    assert {
        "release_gate_evaluated",
        "approval_attempted",
        "release_approved",
        "closeout_generated",
    } <= event_types
