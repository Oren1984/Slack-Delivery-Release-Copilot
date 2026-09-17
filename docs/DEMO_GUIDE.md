# Demo Guide

A short presentation flow for each scenario. Start the app (see
[`OPERATIONS.md`](OPERATIONS.md)), open the Streamlit demo at http://localhost:8501, and select
the scenario from the sidebar.

## 1. Healthy Release (`healthy-release`)

**Narrative:** "Everything shipped clean — here's what a boring, healthy release looks like."

1. **Sprint Convergence tab** — run convergence analysis. Score 100/100, risk Low, no at-risk
   items, no descoping trigger (all work is already Done).
2. **Release Readiness Card tab** — evaluate the gate. Status `READY_FOR_HUMAN_APPROVAL`, every
   check passed. Load the readiness card and show the Block Kit JSON preview.
3. **Human Decision Panel tab** — select actor "Elena Cho" / role "Tech Lead" → **Approve
   Deployment**. Show the success message.
4. **Close-out & Retrospective tab** — generate the close-out report: Say/Do Ratio 100%, sprint
   goal protected, release decision "APPROVED". Generate and show the retrospective draft.
5. **Audit Timeline tab** — show the full sequence of events for this release.

## 2. Descoping Required (`descoping-required`)

**Narrative:** "The sprint is at risk with 36 hours left — here's how the copilot recommends
protecting the goal without touching anything automatically."

1. **Sprint Convergence tab** — run convergence analysis. Score ~50, risk High, several at-risk
   items with explicit reasons.
2. Generate descoping recommendations. Point out: the two goal-critical payment-gateway items are
   **Protect**, three low-priority items are **Candidate for Descoping**, one ambiguous item is
   **Needs Human Review** — and note the caption that nothing changes automatically.
3. Reload the scenario (`GET /api/scenarios/descoping-required`) to show the work items are
   unchanged — the engine only recommended, it didn't act.

## 3. Release Blocked (`release-blocked`)

**Narrative:** "A Blocker-severity data-integrity defect is open — the gate refuses to let this
ship, no matter who asks."

1. **Release Readiness Card tab** — evaluate the gate. Status `HOLD_REQUIRED`, with the open
   Blocker/Critical defects and missing rollback plan listed as blocking reasons.
2. **Human Decision Panel tab** — attempt to approve as "Elena Cho" / "Tech Lead". Show the
   rejection message (the UI surfaces the backend's 409, it does not fake success).
3. **Audit Timeline tab** — show the `approval_rejected` event and that no `release_approved`
   event exists.

## 4. Unauthorized Approval (`unauthorized-approval`)

**Narrative:** "The release is ready to ship — but only the right people can say go."

1. **Release Readiness Card tab** — evaluate the gate. Status `READY_FOR_HUMAN_APPROVAL`.
2. **Human Decision Panel tab** — select actor "Jordan Blake" / role "Observer" → **Approve
   Deployment**. Show the 403 rejection.
3. **Audit Timeline tab** — show the `approval_rejected` event (`outcome: unauthorized_role`).
4. Switch actor to "Elena Cho" / "Tech Lead" and approve successfully, showing the rejection
   didn't corrupt the release's state.

## 5. LLM Failure (`llm-failure`)

**Narrative:** "Even if the optional AI explanation layer breaks, the governance workflow doesn't
stop."

1. **Sprint Convergence** and **Release Readiness Card** tabs — run both; note these never touch
   the LLM layer at all (they're pure deterministic engine output).
2. **Close-out & Retrospective tab** — generate the close-out report (works normally), then
   generate the retrospective draft. Point out the warning banner
   ("LLM explanation layer fell back to the deterministic mock adapter") and that the Markdown
   content is still complete.
3. **Audit Timeline tab** — show the `llm_fallback_used` event.

## Resetting Between Runs

```bash
python scripts/reset_demo.py
```

Clears all audit events, decisions, gate evaluations, and close-out reports so the next
walkthrough starts clean. Scenario data itself is never modified by any workflow, so no
re-seeding step is needed.
