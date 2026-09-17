from __future__ import annotations


def test_e2e_unauthorized_approval_rejected_and_release_stays_unapproved(api_client):
    """Load an otherwise-ready scenario -> an Observer attempts to approve
    -> verify rejection, a governance audit event, and that the release
    remains unapproved."""
    gate = api_client.post(
        "/api/release/evaluate", json={"scenario_id": "unauthorized-approval"}
    ).json()
    assert gate["gate_status"] == "READY_FOR_HUMAN_APPROVAL"

    decision_resp = api_client.post(
        "/api/releases/REL-104/decision",
        json={
            "scenario_id": "unauthorized-approval",
            "actor": "Jordan Blake",
            "role": "Observer",
            "decision": "APPROVED",
        },
    )
    assert decision_resp.status_code == 403

    audit = api_client.get("/api/audit/REL-104").json()
    event_types = {e["event_type"] for e in audit}
    assert "approval_rejected" in event_types
    assert "release_approved" not in event_types

    # A subsequent authorized approval must still be possible — the
    # rejected attempt did not consume or corrupt the release's state.
    authorized_resp = api_client.post(
        "/api/releases/REL-104/decision",
        json={
            "scenario_id": "unauthorized-approval",
            "actor": "Elena Cho",
            "role": "Tech Lead",
            "decision": "APPROVED",
        },
    )
    assert authorized_resp.status_code == 200
