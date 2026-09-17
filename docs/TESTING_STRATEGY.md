# Testing Strategy

## Test Pyramid

```
tests/
├── unit/          57 tests — pure functions and single services, no HTTP layer
├── integration/   17 tests — through the FastAPI TestClient, one call at a time
└── e2e/            5 tests — full multi-step workflows through the API
```

Total: **79 tests**, all passing (`pytest -q`). Every test uses an isolated temporary SQLite
database, reset before each test function (`tests/conftest.py::fresh_database`) — no cross-test
state leakage even though scenario release/sprint IDs are fixed across the suite.

## Unit Tests (`tests/unit/`)

| File | Covers |
|---|---|
| `test_convergence.py` | Convergence scoring, risk classification thresholds, time/dependency/defect penalties, priority/value weighting, uncommitted-item exclusion |
| `test_descoping.py` | Descoping classification rules, sprint-goal protection, Must Hold precedence, trigger conditions, non-mutation guarantee |
| `test_gate.py` | Every release-gate check, category precedence, blocking-defect detection, missing-rollback-plan detection, DoD validation, "never returns deployed" |
| `test_closeout.py` | Say/Do Ratio (including the descoped-items-count-against-the-ratio rule), sprint-goal protection, defect/blocker summaries, repeated-blocker-category matching |
| `test_governance.py` | Role authorization (`is_authorized_to_decide`), actor/role registration matching, role self-assertion rejection |
| `test_approval_service.py` | The full approval state machine: authorized approval, unauthorized rejection, role mismatch, gate-not-ready rejection, missing-evidence rejection, no-gate-evaluation rejection, hold-always-allowed, duplicate-decision rejection |
| `test_llm_fallback.py` | Mock adapter success path, forced-failure fallback, fallback audit event, guarantee that LLM failure never raises to the caller |
| `test_audit.py` | Event persistence, release-scoped filtering, most-recent-first ordering, append-only-by-construction |

## Integration Tests (`tests/integration/test_api.py`)

Every listed endpoint through `TestClient`: scenario listing/retrieval (including 404 on an
unknown scenario), convergence analysis, descoping analysis, gate evaluation (both a ready and a
blocked scenario), the readiness card (including Block Kit action IDs), authorized approval,
unauthorized approval rejection (403), approval rejection for a blocked release (409), close-out
generation, retrospective generation, audit retrieval (unfiltered and release-filtered), health/
ready, and a 422 on an invalid request body.

## End-to-End Tests (`tests/e2e/`)

| File | Scenario | Flow |
|---|---|---|
| `test_e2e_healthy_release.py` | Healthy Release | Load → convergence → gate (`READY_FOR_HUMAN_APPROVAL`) → approve → close-out → verify the full audit trail |
| `test_e2e_descoping_workflow.py` | Descoping Required | Load → convergence (High/Critical risk) → descoping recommendations → verify the scenario's work items are byte-for-byte unchanged |
| `test_e2e_blocked_release.py` | Release Blocked | Load → gate (`HOLD_REQUIRED`) → approval attempt → verify 409 rejection and an `approval_rejected` audit event, with no `release_approved` event ever recorded |
| `test_e2e_unauthorized_approval.py` | Unauthorized Approval | Load → gate ready → Observer approval attempt → verify 403, audit event, and that a subsequent *authorized* approval still succeeds |
| `test_e2e_llm_failure.py` | LLM Failure | `force_llm_failure=true` → verify convergence, gate, and close-out all still complete, the retrospective draft carries `llm_fallback_used: true`, and an `llm_fallback_used` audit event is recorded |

## Running the Suite

```bash
pytest -q                    # all tests
pytest tests/unit -q          # unit only
pytest tests/e2e -q            # e2e only
pytest -q --cov=app            # with coverage (pytest-cov is included)
```

## What Was Deliberately Not Tested

Streamlit UI rendering has no automated test — it is a thin client with no business logic (every
number and status comes from an already-tested API call), so its correctness is covered
transitively by the API tests plus a manual smoke check (`streamlit run demo/streamlit_app.py`).
This keeps the suite meaningful rather than padded, per the project's testing principle.
