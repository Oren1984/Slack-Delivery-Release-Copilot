# Slack Delivery & Release Copilot

A deterministic, human-in-the-loop release-governance copilot for the final 50–100% of the
software delivery lifecycle — sprint convergence, advisory descoping, release-quality gating,
human deployment approval, sprint close-out, and retrospective drafting — demonstrated through a
simulated Slack workflow, entirely offline.

## The Business Problem

By the second half of a sprint, delivery risk shifts from "what should we build" to "will we
finish safely, and should we ship." Teams routinely make three judgment calls under time pressure:
what to descope, whether a release candidate is actually safe, and who gets to say "go." Those
calls are often made informally — in a hallway or a Slack DM — with no consistent evidence trail
and no record of who decided what. That makes release outcomes hard to reproduce, audit, or
improve sprint over sprint.

## The Solution

This project is a **read-only, advisory** engine that turns the evidence already sitting in your
sprint and release data into:

- a deterministic **convergence score and risk level**,
- **advisory descoping recommendations** (never applied automatically),
- a deterministic **release-quality gate** verdict,
- a Slack-style **Release Readiness Card**, and
- an **append-only audit trail** of every analysis, gate evaluation, and approval/hold decision.

A release can only move forward when an explicitly authorized human clicks Approve or Hold. The
system never infers, fabricates, or auto-applies a release decision.

## Position in the SDLC Triangle

This is the third of three companion portfolio projects, together spanning the full SDLC:

| Range | Project | Focus |
|---|---|---|
| 0–25% | ClickUp SDLC Risk Gatekeeper | Requirement readiness, shift-left risk detection |
| 25–50% | Monday Smart PMO Agent | Sprint health, velocity, OKR alignment |
| **50–100%** | **Slack Delivery & Release Copilot (this project)** | Convergence, descoping, release gating, human approval, close-out, retrospective |

See [`docs/SDLC_TRIANGLE.md`](docs/SDLC_TRIANGLE.md) for how the three relate — and why they are
independent, runnable projects rather than an integrated production platform.

## Main Capabilities

- **Sprint convergence analysis** — a 0–100 score, Low/Medium/High/Critical risk level, at-risk
  work items, and a carryover forecast, all from documented deterministic rules.
- **Advisory descoping recommendations** — Protect / Candidate for Descoping / Must Hold /
  Completed / Needs Human Review, each with reasons and a confidence score. Nothing is changed
  automatically.
- **Release quality gate** — READY_FOR_HUMAN_APPROVAL / NOT_READY / HOLD_REQUIRED /
  INSUFFICIENT_EVIDENCE, from checks over defects, QA, DoD, code review, tests, and rollback
  evidence. Never returns "deployed."
- **Release Readiness Card** — a Slack Block Kit-compatible JSON payload with Approve/Hold
  buttons, previewed locally; no real Slack message is ever sent.
- **Human-in-the-loop approval** — only an authorized, registered actor can Approve or Hold; every
  attempt (accepted or rejected) is recorded.
- **Sprint close-out** — Say/Do Ratio, delivered/descoped/carryover counts, defect and blocker
  summaries, and the recorded release decision.
- **Retrospective draft** — deterministic findings assembled into a Markdown/Slack-ready draft;
  an optional LLM layer may only improve wording.
- **Append-only audit trail** — every consequential event, queryable by release.

## Architecture Summary

FastAPI + Pydantic + SQLAlchemy/SQLite backend, a thin Streamlit demo console, and a pure-Python
deterministic domain engine with no framework dependencies. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full component map.

## Governance and Safety Boundaries

- **Read-only and advisory** — no task is closed, no scope is changed, no deployment is executed.
- **Deterministic core** — every calculated value, gate status, and approval rule is plain Python;
  an LLM can never decide, override, or fabricate evidence.
- **Human-in-the-loop** — only Tech Lead / QA Lead actors registered in the scenario data may
  Approve or Hold; unauthorized attempts are rejected and audited.
- **Offline-first** — no real Slack access, no live CI/CD, no production systems; the default LLM
  mode is a fully offline deterministic mock.

Full detail: [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md), [`docs/SECURITY.md`](docs/SECURITY.md),
[`docs/AUDITABILITY.md`](docs/AUDITABILITY.md).

## Quick Start (no Docker)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python scripts/seed_demo.py         # initializes the local SQLite schema

uvicorn app.main:app --reload       # terminal 1 — API on http://localhost:8000
streamlit run demo/streamlit_app.py # terminal 2 — demo UI on http://localhost:8501
```

## Docker (mandatory-supported alternative)

```bash
docker compose up --build
```

This starts the API and the Streamlit demo as two containers sharing a persistent SQLite volume.
Local Python execution (above) remains fully supported for development and troubleshooting — see
[`docs/OPERATIONS.md`](docs/OPERATIONS.md) for both paths in detail.

> **On a network with TLS-inspecting security software** (some antivirus "web protection"
> features, corporate proxies): if the build fails with `SSL: CERTIFICATE_VERIFY_FAILED`, run
> `powershell -File scripts/export_local_ca_cert.ps1` once, then re-run `docker compose up --build`.
> See [`docs/OPERATIONS.md#docker`](docs/OPERATIONS.md#docker) for why this is needed.

## Local URLs

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Streamlit demo | http://localhost:8501 |

## Demo Scenarios

Five synthetic scenarios ship under `data/scenarios/`; load any of them from the Streamlit
sidebar or via `GET /api/scenarios`. See [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md) for a
walkthrough of each.

| Scenario | Expected result |
|---|---|
| Healthy Release | Gate `READY_FOR_HUMAN_APPROVAL`; authorized approval succeeds |
| Descoping Required | High convergence risk; advisory descoping candidates; nothing auto-changed |
| Release Blocked | Gate `HOLD_REQUIRED`; approval attempt rejected |
| Unauthorized Approval | An Observer's approval attempt is rejected and audited |
| LLM Failure | Deterministic analysis completes; LLM layer falls back cleanly |

## Test Commands

```bash
pytest -q          # unit + integration + e2e (79 tests)
ruff check .        # lint
mypy app             # type check
```

See [`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md) for coverage details.

## Project Limitations

This is a POC/MVP: identity and roles are simulated through scenario data, there is no live
Slack/CI/PM-tool integration, and the SQLite store is single-node. See
[`docs/LIMITATIONS_AND_ROADMAP.md`](docs/LIMITATIONS_AND_ROADMAP.md) for the full list and what a
production evolution would require.

## Future Integrations

A real Slack app adapter, a live PM-tool adapter (Monday/ClickUp/Jira), and a real CI/CD
read-only status adapter are documented as optional future extensions — see
[`docs/LIMITATIONS_AND_ROADMAP.md`](docs/LIMITATIONS_AND_ROADMAP.md). None are implemented in
this POC, by design.

## Author

Oren Salmi — portfolio project, third leg of the ClickUp / Monday / Slack SDLC governance
triangle.
