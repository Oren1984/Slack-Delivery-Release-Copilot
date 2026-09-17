# Release Gate Rules

Source of truth: `app/domain/gate.py`. The gate evaluates a `ScenarioDataset` and returns one of
four states — **it never returns "deployed."** The strongest possible outcome,
`READY_FOR_HUMAN_APPROVAL`, only means a human may now make the approval decision.

## Checks and Categories

Every check belongs to exactly one category. Category precedence determines the final gate
status: **blocking_defect > hard_blocking > evidence**.

| Check | Category | Scope | Effect if failed |
|---|---|---|---|
| `no_open_blocker_defects` | blocking_defect | All defects | Forces `HOLD_REQUIRED` |
| `no_open_critical_defects` | blocking_defect | All defects | Forces `HOLD_REQUIRED` |
| `release_critical_qa_complete` | hard_blocking | Work items with `required_for_sprint_goal=true` | Forces `NOT_READY` (unless a blocking_defect check already failed) |
| `dod_complete_for_protected_scope` | hard_blocking | Work items with `required_for_sprint_goal=true` | Forces `NOT_READY` |
| `required_code_reviews_complete` | hard_blocking | All **committed** work items | Forces `NOT_READY` |
| `required_tests_passed` | hard_blocking | `release_candidate.tests_passed` | Forces `NOT_READY` |
| `no_unresolved_mandatory_dependency` | hard_blocking | `release_candidate.unresolved_mandatory_dependencies` | Forces `NOT_READY` |
| `release_notes_available` | evidence | `release_candidate.release_notes_available` | Forces `INSUFFICIENT_EVIDENCE` (unless a higher-precedence check already failed) |
| `rollback_plan_available` | evidence | `release_candidate.rollback_plan_available` | Forces `INSUFFICIENT_EVIDENCE` |
| `rollback_owner_identified` | evidence | `release_candidate.rollback_owner` non-empty | Forces `INSUFFICIENT_EVIDENCE` |
| `monitoring_plan_available` | evidence | `release_candidate.monitoring_plan_available` | Forces `INSUFFICIENT_EVIDENCE` |

**Design note:** `required_code_reviews_complete` checks *every committed item*, not only
sprint-goal items — a release candidate should not ship with unreviewed code anywhere in its
scope, even on lower-priority work.

## Resulting Gate Status (precedence, highest wins)

1. **`HOLD_REQUIRED`** — one or more open Blocker/Critical defects exist. Nothing else matters
   until they are resolved; this is the only state where a release is actively unsafe.
2. **`NOT_READY`** — no blocking defects, but a hard-blocking check (QA, DoD, code review, tests,
   or mandatory dependency) failed. The work isn't done yet.
3. **`INSUFFICIENT_EVIDENCE`** — all hard-blocking checks passed, but required release evidence
   (notes, rollback plan/owner, monitoring plan) is missing. The work is done; the paperwork
   isn't.
4. **`READY_FOR_HUMAN_APPROVAL`** — every check passed. A human may now record an Approve or Hold
   decision — see [`GOVERNANCE.md`](GOVERNANCE.md#human-in-the-loop-approval).

## Result Payload

Every evaluation returns: `passed_checks`, `failed_checks`, `missing_evidence` (the evidence-
category subset of failed checks), `blocking_reasons` (human-readable detail strings for whatever
category determined the final status), `warnings` (evidence gaps that did **not** determine the
final status, e.g. when a hard-blocking failure already forced `NOT_READY`), and a
`recommended_next_action` string tailored to the resulting status. Every evaluation is persisted
(`gate_evaluations` table) and produces a `release_gate_evaluated` audit event — see
[`AUDITABILITY.md`](AUDITABILITY.md).
