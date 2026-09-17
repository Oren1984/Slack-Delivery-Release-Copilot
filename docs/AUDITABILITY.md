# Auditability

## Model

Every audit event (`app/models/orm.py::AuditEventRecord`) carries: `id`, `event_type`,
`timestamp` (UTC), `actor`, `actor_role`, `sprint_id`, `release_id`, `evidence_reference`,
`previous_state`, `new_state`, `reason`, `outcome`, and `correlation_id`. Nothing sensitive
(secrets, environment values, full request payloads) is ever written to any of these fields — see
[`SECURITY.md`](SECURITY.md#safe-logging).

## Append-Only Guarantee

`app/repositories/audit_repo.py` exposes exactly two functions: `append_event` and `list_events`.
There is no `update_event` or `delete_event` anywhere in the codebase — the trail is append-only
**at the application level** by construction, not by a database trigger. This is directly
verified by `tests/unit/test_audit.py::test_audit_table_has_no_update_or_delete_helpers`.

The same pattern applies to `human_decisions`: a later decision attempt is always a **new row**,
never an update to a prior one. Every attempt — accepted or rejected — remains visible via
`GET /api/audit/{release_id}`, satisfying "repeated decisions must remain visible in the audit
trail."

## Event Catalog

| Event type | Emitted by | Meaning |
|---|---|---|
| `dataset_loaded` | `POST /api/convergence/analyze` | A scenario was read for analysis |
| `convergence_analysis_completed` | `convergence_service` | Stage B ran |
| `descoping_recommendation_generated` | `descoping_service` | Stage C ran |
| `release_gate_evaluated` | `gate_service` | Stage D ran; `outcome` = resulting gate status |
| `approval_attempted` | `approval_service` | Any decision submission, before validation |
| `approval_rejected` | `approval_service` | A decision was rejected; `outcome` names the reason (`unauthorized_role`, `actor_role_mismatch`, `duplicate_decision`, `no_gate_evaluation`, `missing_evidence`, `gate_not_ready`) |
| `release_approved` | `approval_service` | An APPROVED decision was accepted |
| `release_held` | `approval_service` | A HELD decision was accepted |
| `closeout_generated` | `closeout_service` | Stage G ran |
| `llm_fallback_used` | `llm_explanation_service` | The LLM layer fell back to the deterministic mock |

## Correlation IDs

Every HTTP request is assigned a correlation ID (incoming `X-Correlation-ID` header if present,
otherwise generated) by middleware in `app/main.py`, stored in a context variable
(`app/core/logging.py`), echoed back in the response header, and attached to every audit event and
structured log line produced during that request — so a single request's full effect (log lines +
audit events) can be reconstructed from one ID.

## Retrieval

- `GET /api/audit` — every event, most recent first.
- `GET /api/audit/{release_id}` — events scoped to one release, most recent first.

Both are backed by `services/audit_service.py::list_audit_events`, which is the only read path
onto the table exposed via the API.
