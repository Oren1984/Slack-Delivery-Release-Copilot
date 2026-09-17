"""Slack Delivery & Release Copilot — local demo console.

Thin Streamlit client over the FastAPI backend. This UI performs no business
logic of its own: every number, status, and decision outcome shown here
comes directly from an API call, and a backend rejection is always shown as
a rejection — never silently treated as success.
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Slack Delivery & Release Copilot", layout="wide")


def api_get(path: str, **kwargs) -> tuple[int, dict]:
    try:
        resp = httpx.get(f"{API_BASE_URL}{path}", timeout=15, **kwargs)
        return resp.status_code, resp.json()
    except httpx.HTTPError as exc:
        return 0, {"detail": f"Could not reach API at {API_BASE_URL}: {exc}"}


def api_post(path: str, json: dict) -> tuple[int, dict]:
    try:
        resp = httpx.post(f"{API_BASE_URL}{path}", json=json, timeout=15)
        return resp.status_code, resp.json()
    except httpx.HTTPError as exc:
        return 0, {"detail": f"Could not reach API at {API_BASE_URL}: {exc}"}


st.title("Slack Delivery & Release Copilot")
st.caption(
    "Read-only · Advisory · Offline-first · Human-in-the-loop — no real Slack messages "
    "or deployments are ever sent from this console."
)

status_code, scenarios = api_get("/api/scenarios")
if status_code != 200:
    st.error(f"Could not load scenarios from the API: {scenarios.get('detail', scenarios)}")
    st.stop()

scenario_labels = {f"{s['title']} ({s['scenario_id']})": s for s in scenarios}
selected_label = st.sidebar.selectbox("Scenario", list(scenario_labels.keys()))
scenario_meta = scenario_labels[selected_label]
scenario_id = scenario_meta["scenario_id"]
release_id = scenario_meta["release_id"]
sprint_id = scenario_meta["sprint_id"]

st.sidebar.markdown(f"**Sprint:** `{sprint_id}`")
st.sidebar.markdown(f"**Release:** `{release_id}`")

tabs = st.tabs(
    [
        "Sprint Convergence",
        "Release Readiness Card",
        "Human Decision Panel",
        "Close-out & Retrospective",
        "Audit Timeline",
    ]
)

# --- Sprint Convergence ---
with tabs[0]:
    st.subheader("Sprint Convergence")
    if st.button("Run convergence analysis", key="run_convergence"):
        code, convergence = api_post("/api/convergence/analyze", {"scenario_id": scenario_id})
        st.session_state["convergence"] = (code, convergence)

    if "convergence" in st.session_state:
        code, convergence = st.session_state["convergence"]
        if code != 200:
            st.error(convergence.get("detail", "Convergence analysis failed."))
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Convergence score", f"{convergence['convergence_score']}/100")
            c2.metric("Risk level", convergence["risk_level"])
            c3.metric("Hours remaining", convergence["hours_remaining"])
            st.info(convergence["recommended_action"])

            st.markdown("**At-risk work items**")
            if convergence["at_risk_items"]:
                st.table(
                    [
                        {
                            "ID": i["work_item_id"],
                            "Title": i["title"],
                            "Completion ratio": i["completion_ratio"],
                            "Reasons": "; ".join(i["reasons"]),
                        }
                        for i in convergence["at_risk_items"]
                    ]
                )
            else:
                st.write("None.")

            st.markdown("**Carryover forecast**")
            st.write(convergence["carryover_forecast"] or "None.")

    st.divider()
    st.subheader("Descoping Recommendations (Advisory Only)")
    if st.button("Generate descoping recommendations", key="run_descoping"):
        code, descoping = api_post("/api/convergence/descope", {"scenario_id": scenario_id})
        st.session_state["descoping"] = (code, descoping)

    if "descoping" in st.session_state:
        code, descoping = st.session_state["descoping"]
        if code != 200:
            st.error(descoping.get("detail", "Descoping analysis failed."))
        else:
            st.write(
                f"Triggered: **{descoping['triggered']}** — "
                + ("; ".join(descoping["trigger_reasons"]) or "No trigger conditions met.")
            )
            st.table(
                [
                    {
                        "ID": r["work_item_id"],
                        "Title": r["title"],
                        "Recommendation": r["recommendation"],
                        "Confidence": r["confidence"],
                        "Reasons": "; ".join(r["reasons"]),
                    }
                    for r in descoping["recommendations"]
                ]
            )
            st.caption(
                "These are recommendations only. No work item is changed automatically — a "
                "human must accept or reject each one."
            )

# --- Release Readiness Card ---
with tabs[1]:
    st.subheader("Release Readiness Card")
    if st.button("Evaluate release gate", key="run_gate"):
        code, gate = api_post("/api/release/evaluate", {"scenario_id": scenario_id})
        st.session_state["gate"] = (code, gate)

    if st.button("Load readiness card", key="load_card"):
        code, card = api_get(f"/api/releases/{release_id}/readiness-card")
        st.session_state["card"] = (code, card)

    if "gate" in st.session_state:
        code, gate = st.session_state["gate"]
        if code != 200:
            st.error(gate.get("detail", "Gate evaluation failed."))
        else:
            status = gate["gate_status"]
            color = {
                "READY_FOR_HUMAN_APPROVAL": "green",
                "NOT_READY": "orange",
                "HOLD_REQUIRED": "red",
                "INSUFFICIENT_EVIDENCE": "orange",
            }.get(status, "gray")
            st.markdown(f"**Gate status:** :{color}[{status}]")
            st.write(f"Recommended next action: {gate['recommended_next_action']}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Passed checks**")
                for c in gate["passed_checks"]:
                    st.write(f"✅ {c['name']} — {c['detail']}")
            with col2:
                st.markdown("**Failed checks**")
                for c in gate["failed_checks"]:
                    st.write(f"❌ {c['name']} — {c['detail']}")

    if "card" in st.session_state:
        code, card = st.session_state["card"]
        if code != 200:
            st.error(card.get("detail", "Could not load readiness card."))
        else:
            st.divider()
            st.markdown(f"### {card['version']} — {card['sprint_name']}")
            st.json(card["block_kit"], expanded=False)

# --- Human Decision Panel ---
with tabs[2]:
    st.subheader("Human Decision Panel")
    code, full_scenario = api_get(f"/api/scenarios/{scenario_id}")
    actors = full_scenario.get("authorized_actors", []) if code == 200 else []

    actor_name = (
        st.selectbox("Actor", [a["name"] for a in actors]) if actors else st.text_input("Actor")
    )
    role_options = sorted({a["role"] for a in actors}) or [
        "Tech Lead",
        "QA Lead",
        "Delivery Manager",
        "Observer",
    ]
    role = st.selectbox("Role", role_options)
    reason = st.text_input("Reason (optional, used for Hold)")

    col1, col2 = st.columns(2)
    with col1:
        approve_clicked = st.button("Approve Deployment", type="primary")
    with col2:
        hold_clicked = st.button("Hold Release")

    if approve_clicked or hold_clicked:
        decision = "APPROVED" if approve_clicked else "HELD"
        try:
            resp = httpx.post(
                f"{API_BASE_URL}/api/releases/{release_id}/decision",
                json={
                    "scenario_id": scenario_id,
                    "actor": actor_name,
                    "role": role,
                    "decision": decision,
                    "reason": reason or None,
                },
                timeout=15,
            )
            result = resp.json()
        except httpx.HTTPError as exc:
            resp, result = None, {"detail": f"Could not reach API: {exc}"}

        if resp is not None and resp.status_code == 200:
            st.success(
                f"Decision recorded: {result['decision']} by {result['actor']} ({result['role']})."
            )
        else:
            status = resp.status_code if resp is not None else "no response"
            st.error(f"Decision rejected ({status}): {result.get('detail')}")

# --- Close-out & Retrospective ---
with tabs[3]:
    st.subheader("Sprint Close-out")
    if st.button("Generate close-out report"):
        code, report = api_post(f"/api/sprints/{sprint_id}/close-out", {"scenario_id": scenario_id})
        st.session_state["closeout"] = (code, report)

    if "closeout" in st.session_state:
        code, report = st.session_state["closeout"]
        if code != 200:
            st.error(report.get("detail", "Close-out generation failed."))
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Planned", report["planned_count"])
            c2.metric("Delivered", report["delivered_count"])
            c3.metric("Descoped", report["descoped_count"])
            c4.metric("Carryover", report["carryover_count"])
            st.metric("Say/Do Ratio", f"{report['say_do_ratio']}%")
            st.write(f"Sprint goal protected: **{report['sprint_goal_protected']}**")
            st.write(f"Release decision: **{report['release_decision'] or 'Not yet decided'}**")
            st.markdown("**Operational lessons**")
            for lesson in report["operational_lessons"]:
                st.write(f"- {lesson}")

    st.divider()
    st.subheader("Retrospective Draft")
    if st.button("Generate retrospective draft"):
        code, draft = api_post(
            f"/api/sprints/{sprint_id}/retrospective", {"scenario_id": scenario_id}
        )
        st.session_state["retro"] = (code, draft)

    if "retro" in st.session_state:
        code, draft = st.session_state["retro"]
        if code != 200:
            st.error(draft.get("detail", "Retrospective generation failed."))
        else:
            if draft["llm_fallback_used"]:
                st.warning("LLM explanation layer fell back to the deterministic mock adapter.")
            st.markdown(draft["markdown"])
            st.download_button(
                "Download retrospective (Markdown)",
                draft["markdown"],
                file_name=f"retrospective_{sprint_id}.md",
            )

# --- Audit Timeline ---
with tabs[4]:
    st.subheader("Audit Timeline")
    scope = st.radio("Scope", ["This release", "All releases"], horizontal=True)
    path = f"/api/audit/{release_id}" if scope == "This release" else "/api/audit"
    code, events = api_get(path)
    if code != 200:
        st.error(events.get("detail", "Could not load audit events."))
    else:
        st.table(
            [
                {
                    "Time (UTC)": e["timestamp"],
                    "Event": e["event_type"],
                    "Outcome": e["outcome"],
                    "Actor": e["actor"] or "-",
                    "Role": e["actor_role"] or "-",
                    "Release": e["release_id"] or "-",
                    "Reason": e["reason"] or "-",
                }
                for e in events
            ]
        )
