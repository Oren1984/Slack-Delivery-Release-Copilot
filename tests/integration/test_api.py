from __future__ import annotations


def test_list_scenarios(api_client):
    resp = api_client.get("/api/scenarios")
    assert resp.status_code == 200
    ids = {s["scenario_id"] for s in resp.json()}
    assert {
        "healthy-release",
        "descoping-required",
        "release-blocked",
        "unauthorized-approval",
        "llm-failure",
    } <= ids


def test_get_single_scenario(api_client):
    resp = api_client.get("/api/scenarios/healthy-release")
    assert resp.status_code == 200
    assert resp.json()["sprint"]["id"] == "SPR-101"


def test_get_unknown_scenario_returns_404(api_client):
    resp = api_client.get("/api/scenarios/does-not-exist")
    assert resp.status_code == 404


def test_convergence_analysis_through_api(api_client):
    resp = api_client.post("/api/convergence/analyze", json={"scenario_id": "healthy-release"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sprint_id"] == "SPR-101"
    assert body["convergence_score"] == 100.0
    assert body["risk_level"] == "Low"


def test_descoping_analysis_through_api(api_client):
    resp = api_client.post("/api/convergence/descope", json={"scenario_id": "descoping-required"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["triggered"] is True
    assert len(body["recommendations"]) > 0


def test_gate_evaluation_through_api(api_client):
    resp = api_client.post("/api/release/evaluate", json={"scenario_id": "healthy-release"})
    assert resp.status_code == 200
    assert resp.json()["gate_status"] == "READY_FOR_HUMAN_APPROVAL"


def test_gate_evaluation_blocked_release_through_api(api_client):
    resp = api_client.post("/api/release/evaluate", json={"scenario_id": "release-blocked"})
    assert resp.status_code == 200
    assert resp.json()["gate_status"] == "HOLD_REQUIRED"


def test_readiness_card_endpoint(api_client):
    resp = api_client.get("/api/releases/REL-101/readiness-card")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "v2.9.0"
    assert "blocks" in body["block_kit"]
    action_ids = {
        el["action_id"]
        for block in body["block_kit"]["blocks"]
        if block["type"] == "actions"
        for el in block["elements"]
    }
    assert {"approve_deployment", "hold_release"} <= action_ids


def test_authorized_approval_through_api(api_client):
    api_client.post("/api/release/evaluate", json={"scenario_id": "healthy-release"})
    resp = api_client.post(
        "/api/releases/REL-101/decision",
        json={
            "scenario_id": "healthy-release",
            "actor": "Elena Cho",
            "role": "Tech Lead",
            "decision": "APPROVED",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "APPROVED"


def test_unauthorized_approval_rejected_through_api(api_client):
    api_client.post("/api/release/evaluate", json={"scenario_id": "unauthorized-approval"})
    resp = api_client.post(
        "/api/releases/REL-104/decision",
        json={
            "scenario_id": "unauthorized-approval",
            "actor": "Jordan Blake",
            "role": "Observer",
            "decision": "APPROVED",
        },
    )
    assert resp.status_code == 403


def test_approval_rejected_for_blocked_release_through_api(api_client):
    api_client.post("/api/release/evaluate", json={"scenario_id": "release-blocked"})
    resp = api_client.post(
        "/api/releases/REL-103/decision",
        json={
            "scenario_id": "release-blocked",
            "actor": "Elena Cho",
            "role": "Tech Lead",
            "decision": "APPROVED",
        },
    )
    assert resp.status_code == 409


def test_closeout_generation_through_api(api_client):
    resp = api_client.post(
        "/api/sprints/SPR-101/close-out", json={"scenario_id": "healthy-release"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["say_do_ratio"] == 100.0
    assert body["sprint_goal_protected"] is True


def test_retrospective_generation_through_api(api_client):
    resp = api_client.post(
        "/api/sprints/SPR-101/retrospective", json={"scenario_id": "healthy-release"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Retrospective" in body["markdown"]
    assert body["llm_fallback_used"] is False


def test_audit_retrieval_through_api(api_client):
    api_client.post("/api/convergence/analyze", json={"scenario_id": "healthy-release"})
    resp = api_client.get("/api/audit")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_audit_retrieval_filtered_by_release(api_client):
    api_client.post("/api/release/evaluate", json={"scenario_id": "healthy-release"})
    resp = api_client.get("/api/audit/REL-101")
    assert resp.status_code == 200
    body = resp.json()
    assert all(e["release_id"] == "REL-101" for e in body)
    assert any(e["event_type"] == "release_gate_evaluated" for e in body)


def test_health_and_ready_endpoints(api_client):
    assert api_client.get("/health").status_code == 200
    assert api_client.get("/ready").status_code == 200


def test_invalid_request_body_returns_422(api_client):
    resp = api_client.post("/api/convergence/analyze", json={})
    assert resp.status_code == 422
