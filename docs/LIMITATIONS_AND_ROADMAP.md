# Limitations & Future Improvements

## Known Limitations (by design, for a POC/MVP)

- **Identity and roles are simulated.** `authorized_actors` is part of each scenario's JSON file;
  there is no real authentication/SSO layer. This is appropriate for a local demo but would need
  a real identity provider before any production use.
- **No live integrations.** No real Slack workspace, no live PM tool (Jira/Monday/ClickUp), no
  real CI/CD system, and no production monitoring system are connected. Everything runs against
  synthetic local JSON data.
- **Single-node SQLite.** Fine for a local demo; would need a networked database (e.g. Postgres)
  for any multi-instance or concurrent-write deployment.
- **Scenario data is static per request.** There is no mechanism for a scenario file to be
  updated mid-demo by an external event feed — a new "convergence analysis" simply re-reads the
  same JSON file unless you edit it yourself.
- **The `openai_compatible` LLM adapter is unauthenticated-by-caller.** Any process with access to
  the configured environment variables can trigger LLM calls; there's no per-request LLM-usage
  authorization layer (acceptable for a single-operator local POC).
- **Role-to-approval mapping is an interpretation.** The product spec describes role
  responsibilities but doesn't enumerate an explicit "who may approve" list; this implementation
  chose Tech Lead + QA Lead (documented in `docs/GOVERNANCE.md`) — a real deployment should
  confirm this against actual organizational policy.

## Future Integrations (documented, not implemented)

These are natural extension points given the adapter pattern already in place
(`docs/ARCHITECTURE.md#adapter-pattern`) — none are built in this POC:

- **Real Slack API adapter** — would implement the same `send()`-style interface as
  `MockSlackAdapter` but call the Slack Web API; the Block Kit payload format already produced by
  `slack_adapter.py` would not need to change.
- **PM-tool adapter (Monday / ClickUp / Jira)** — would replace `LocalDatasetAdapter` with a live
  data source implementing the same `load()` / `find_by_release_id()` interface, feeding real
  sprint/work-item data into the unchanged deterministic engine.
- **GitHub/Azure DevOps adapter** — would supply real code-review and CI status instead of the
  scenario's `code_review_status` / `tests_passed` fields.
- **Read-only CI/CD status adapter** — could surface a real build/deploy pipeline's status inside
  the readiness card without ever triggering a deployment from this system.

## What Would Need to Change for Production

1. A real identity/authentication layer replacing the scenario-embedded `authorized_actors` list.
2. A networked, backed-up database instead of file-based SQLite.
3. Structured log shipping to a real observability backend (the JSON log format is already
   compatible with most log aggregators).
4. A secrets manager for the `openai_compatible` API key instead of a plain environment variable.
5. Real integrations per the adapter list above, each behind its own authorization and rate
   limiting.
