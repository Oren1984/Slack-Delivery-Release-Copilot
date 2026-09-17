from __future__ import annotations


def test_e2e_blocked_release_approval_is_rejected_and_audited(api_client):
    """Load scenario -> evaluate gate -> attempt approval -> verify
    rejection and audit event."""
    gate = api_client.post("/api/release/evaluate", json={"scenario_id": "release-blocked"}).json()
    assert gate["gate_status"] == "HOLD_REQUIRED"

    decision_resp = api_client.post(
        "/api/releases/REL-103/decision",
        json={
            "scenario_id": "release-blocked",
            "actor": "Elena Cho",
            "role": "Tech Lead",
            "decision": "APPROVED",
        },
    )
    assert decision_resp.status_code == 409

    audit = api_client.get("/api/audit/REL-103").json()
    event_types = {e["event_type"] for e in audit}
    assert "approval_rejected" in event_types
    assert not any(e["event_type"] == "release_approved" for e in audit)
