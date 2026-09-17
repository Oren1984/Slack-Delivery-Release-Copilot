# Observability

## Structured Logs

`app/core/logging.py` configures a JSON log formatter on the root logger: every line includes
`level`, `logger`, `message`, and `correlation_id`. No secrets or request payloads are logged —
see [`SECURITY.md`](SECURITY.md#safe-logging).

## Request Correlation IDs

Middleware in `app/main.py` assigns a correlation ID per request (reusing an incoming
`X-Correlation-ID` header when present), stores it in a `contextvars.ContextVar`
(`app/core/logging.py::correlation_id_var`), attaches it to every log line and audit event
produced while handling that request, and echoes it back as a response header.

## Health and Readiness

| Endpoint | Purpose | Behavior |
|---|---|---|
| `GET /health` | Liveness | Always `200 {"status": "ok"}` if the process is running |
| `GET /ready` | Readiness | `200` if the SQLite connection is reachable, `503` otherwise |

Docker Compose's `api` service healthcheck polls `/health` (see
[`OPERATIONS.md`](OPERATIONS.md#docker)).

## Metrics

`GET /metrics` exposes Prometheus-compatible counters (`app/core/metrics.py`, its own isolated
`CollectorRegistry` so it never mixes with global Prometheus state):

| Metric | Incremented when |
|---|---|
| `convergence_analyses_total` | A convergence analysis completes |
| `gate_evaluations_total` | A release gate evaluation completes |
| `release_approvals_total` | A release is approved |
| `release_holds_total` | A release is held |
| `rejected_approval_attempts_total` | Any decision attempt is rejected (unauthorized, duplicate, gate-not-ready, etc.) |
| `llm_fallbacks_total` | The LLM layer falls back to the deterministic mock adapter |

These are intentionally the six counters the product spec calls out — no additional metrics
infrastructure (histograms, custom exporters, a Grafana stack) is included, consistent with
keeping the POC proportionate.

## Error Handling

Three global exception handlers in `app/main.py`:

1. `CopilotError` → the exception's own `status_code` and `message` (e.g. 403 for an
   unauthorized approval, 409 for a duplicate decision).
2. `RequestValidationError` (Pydantic/FastAPI request validation) → `422` with a generic message.
3. Any other `Exception` → `500` with a generic message; the exception type (not its message or
   traceback) is logged server-side for debugging.

No handler ever returns a raw stack trace or exception message from unexpected errors to the
caller.
