from __future__ import annotations

import copy


def test_e2e_descoping_workflow_never_mutates_source_data(api_client):
    """Load scenario -> detect risk -> produce recommendations -> verify no
    work item was automatically changed by the recommendation engine."""
    before = api_client.get("/api/scenarios/descoping-required").json()
    before_items = copy.deepcopy(before["work_items"])

    convergence = api_client.post(
        "/api/convergence/analyze", json={"scenario_id": "descoping-required"}
    ).json()
    assert convergence["risk_level"] in ("High", "Critical")

    descoping = api_client.post(
        "/api/convergence/descope", json={"scenario_id": "descoping-required"}
    ).json()
    assert descoping["triggered"] is True
    recommendation_types = {r["recommendation"] for r in descoping["recommendations"]}
    assert "Candidate for Descoping" in recommendation_types
    assert all(
        r["human_decision_required"] or r["recommendation"] == "Completed"
        for r in descoping["recommendations"]
    )

    after = api_client.get("/api/scenarios/descoping-required").json()
    assert after["work_items"] == before_items
