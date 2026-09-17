# Security Controls

## Input Validation

Every external input is validated by Pydantic before it reaches business logic:

- Scenario JSON files are validated against `ScenarioDataset` (`app/schemas/dataset.py`),
  including cross-reference checks (defect → work item, dependency → work item). A malformed file
  raises `ValidationFailedError` (HTTP 422), never an unhandled exception.
- Every API request body is a typed Pydantic model (`app/schemas/requests.py`) with
  `extra="forbid"`, so unexpected fields are rejected rather than silently ignored.

## Role Validation

Approval/hold authorization is enforced server-side in `app/services/approval_service.py` and
`app/services/governance.py` — never trusted from client input alone. An actor must be registered
in the scenario's `authorized_actors` list under the exact role claimed; role self-assertion
(claiming a role you're not registered under) is rejected. See
[`GOVERNANCE.md`](GOVERNANCE.md#human-in-the-loop-approval).

## No Hardcoded Secrets

No API key, token, or credential is hardcoded anywhere in the codebase. `.env.example` documents
every environment variable with empty/placeholder defaults; `.env` and `*.db` are gitignored.

## Safe Logging

`app/core/logging.py` emits structured JSON logs with a correlation ID but never logs request
bodies, environment variable values, or the OpenAI-compatible API key. Error handlers in
`app/main.py` return a generic message to the caller and log only the exception type internally —
never a raw traceback to the client.

## Offline Boundaries

- **No real Slack access**: `MockSlackAdapter.send()` performs no network call under any
  configuration; there is no code path that reaches a real Slack workspace.
- **No arbitrary file access**: the dataset adapter only reads `*.json` files from the configured
  `SCENARIOS_DIR`; no endpoint accepts an arbitrary file path from a client.
- **No command execution from user input**: no endpoint or service shells out to the OS based on
  request data.
- **No automatic deployment**: see [`GOVERNANCE.md`](GOVERNANCE.md#no-automatic-deployment).
- **No external network calls in offline (default) mode**: `LLM_MODE=mock` is the default and
  performs no network I/O. The only optional network call in the entire system is the
  `openai_compatible` LLM adapter, and it is disabled unless explicitly configured.

## Opt-In External LLM

If `LLM_MODE=openai_compatible` is set, `OPENAI_COMPATIBLE_BASE_URL`, `_API_KEY`, and `_MODEL`
must all be provided or the adapter refuses to initialize and the system falls back to the mock
adapter. The API key is read from the environment only, at request time, and is never logged,
returned in an API response, or persisted to the database.

## Deployment Guarantees Carried Over From Governance

Least-privilege and read-only-by-default boundaries are enforced by construction (see
[`ARCHITECTURE.md`](ARCHITECTURE.md) for the adapter pattern that isolates every external
touchpoint) rather than by runtime permission checks against a live system — there is no live
system to check against in this POC.
