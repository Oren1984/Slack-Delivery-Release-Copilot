# Governance

## Read-Only Boundary

The system reads local scenario data and its own audit/decision history. It never:

- closes or changes the status of a work item,
- changes sprint scope,
- triggers a real deployment or CI/CD action,
- accesses a production system, or
- sends a real Slack message (the Slack adapter is mock-only; see
  [`SECURITY.md`](SECURITY.md#offline-boundaries)).

Descoping recommendations are advisory text only — `app/domain/descoping.py` returns a result
object and never writes back to a work item. This is enforced by construction (the function has
no mutation path to the input) and verified by `tests/e2e/test_e2e_descoping_workflow.py`, which
asserts the scenario is byte-for-byte identical before and after a descoping analysis.

## Human-in-the-Loop Approval

- Only an actor registered in the scenario's `authorized_actors` list, under the **exact role**
  they claim, may submit a decision — role self-assertion is rejected
  (`app/services/governance.py::actor_has_role`).
- Of the four product roles, only **Tech Lead** and **QA Lead** may Approve or Hold
  (`AUTHORIZED_DECISION_ROLES`). Delivery Manager/PMO owns scope and convergence tracking, not the
  go/no-go call; Observer is explicitly read-only. This is a documented interpretation of the
  product's role descriptions — see the comment in `app/services/governance.py` for the rationale
  — and is covered by `tests/unit/test_governance.py`.
- **APPROVED** requires a prior gate evaluation on record with status
  `READY_FOR_HUMAN_APPROVAL`. `INSUFFICIENT_EVIDENCE` rejects with a `MissingEvidenceError`; any
  other non-ready status rejects with an `InvalidReleaseTransitionError`; no evaluation on record
  at all also rejects.
- **HELD** is always permitted for an authorized actor, regardless of gate status, with an
  optional reason — holding a release is never unsafe.
- Once a release has an **accepted** decision, every further attempt is rejected as a duplicate
  (`DuplicateDecisionError`) — a decision cannot be silently overwritten.
- Every attempt — accepted or rejected — is persisted in the `human_decisions` table and produces
  an `approval_attempted` audit event, followed by `release_approved` / `release_held` /
  `approval_rejected`. Nothing is ever deleted or updated in place; the full history of attempts
  for a release remains visible via `GET /api/audit/{release_id}`.

The approval decision represents permission to *continue* an external deployment process that is
entirely outside this system's scope. **The system never executes a deployment.**

## AI Limitations

The LLM explanation layer (`app/adapters/llm/`) may only reword already-finalized deterministic
findings — executive summaries, blocker summaries, descoping explanations, and retrospective
intros. Its system prompt (`OpenAICompatibleLLMAdapter.SYSTEM_PROMPT`) explicitly forbids
inventing facts, changing any number or status, or suggesting an approval/hold decision. No
service function ever uses an LLM's output to set a gate status, a decision, or a calculated
value — those are always computed by `app/domain/` first and passed to the LLM layer as
already-final context.

## Failure Handling

- A malformed or incomplete scenario file produces a controlled `ValidationFailedError` (HTTP
  422), never an unhandled exception.
- An LLM failure or invalid response is caught inside `explain_with_fallback` and never propagates
  — the deterministic result is always returned, with a fallback explanation and an audit event.
- Every `CopilotError` subclass carries a fixed, user-safe message and HTTP status; the global
  exception handler in `app/main.py` converts any unexpected exception to a generic 500 without
  leaking a stack trace.

## No Automatic Deployment

There is no code path anywhere in this repository that calls a deployment API, a CI/CD trigger,
or a real Slack API. The "Approve Deployment" action in the UI and the Block Kit card is a label
on a human decision record — nothing more.
