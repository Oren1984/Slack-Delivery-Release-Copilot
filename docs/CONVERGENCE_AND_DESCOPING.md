# Sprint Convergence & Descoping Rules

Source of truth: `app/domain/convergence.py` and `app/domain/descoping.py`. Both stages are pure
functions over a validated `ScenarioDataset` — no I/O, no randomness, reproducible for identical
input.

## Sprint Convergence (Stage B)

### 1. Per-item completion ratio

Every **committed** work item starts from a status-based base ratio:

| Status | Base ratio |
|---|---|
| Done | 1.00 |
| In QA | 0.85 |
| In Code Review | 0.60 |
| In Progress | 0.35 |
| Not Started | 0.05 |
| Blocked | 0.00 |

For any item not yet `Done`, the base ratio is then penalized (multiplicatively, and
penalties stack) when:

- **Time risk**: `estimated_remaining_hours > hours_remaining × 0.8` → ratio ×= 0.5. ("Can this
  realistically fit in the time left, with a 20% safety margin?")
- **Unresolved dependency**: `blocking_dependency_ids` is non-empty → ratio ×= 0.5.
- **Linked blocking defect**: the item is referenced by an open Blocker or Critical defect →
  ratio ×= 0.5.

`hours_remaining` is `sprint.end_date - simulated_now`, floored at 0.

### 2. Convergence score

Each item is weighted by `priority_weight × business_value_weight` (Critical=4/High=3/Medium=2/
Low=1 on each axis). The score is the weighted average of completion ratios, scaled to 0–100:

```
score = (Σ ratio_i × weight_i) / (Σ weight_i) × 100
```

Uncommitted items (`committed: false`) are excluded entirely — they were never part of the
sprint's delivery commitment.

### 3. Risk level

| Score | Risk level |
|---|---|
| ≥ 80 | Low |
| ≥ 60 | Medium |
| ≥ 40 | High |
| < 40 | Critical |

### 4. At-risk items and carryover forecast

- **At-risk**: not `Done` and completion ratio < 0.60.
- **Carryover forecast**: not `Done` and completion ratio < 0.50.

### 5. Recommended action by risk level

| Risk level | Recommended action |
|---|---|
| Low | Proceed as planned; continue routine monitoring. |
| Medium | Monitor at-risk items closely; prepare contingency plans. |
| High | Initiate a descoping review with the Delivery Manager and Tech Lead. |
| Critical | Escalate immediately: convene stakeholders and review descoping candidates. |

## Descoping Recommendations (Stage C)

### Trigger conditions (either fires the stage)

- Sprint ends within **48 hours** of `simulated_now`, or
- Convergence risk level is **High** or **Critical**.

The trigger only controls whether the stage is presented as active in the API/UI; recommendations
are always computable on demand.

### Per-item classification (first matching rule wins)

1. **Completed** — status is `Done`.
2. **Must Hold** — `required_for_sprint_goal` is true AND (linked to an open Blocker/Critical
   defect OR blocked/dependency-stuck with completion ratio < 0.5). Incomplete and unsafe to ship.
3. **Protect** — `required_for_sprint_goal` is true (and rule 2 didn't match). Never a descoping
   candidate.
4. **Candidate for Descoping** — not required for the goal, AND either:
   - priority ∈ {Low, Medium} AND business value ∈ {Low, Medium} AND status ∈ {Not Started, In
     Progress} (all three low-signal conditions), or
   - blocked/dependency-stuck with completion ratio < 0.5 (even if it doesn't match all three
     conditions above).
5. **Needs Human Review** — none of the above matched confidently. The deterministic engine
   defers to a human rather than guessing.

Each recommendation carries a **confidence** score (rule-coverage based: more matched conditions
→ higher confidence) and `human_decision_required: true` for every non-`Completed` item.

### Guarantee

The descoping engine **never mutates any work item**. It reads `ScenarioDataset` and returns a
`DescopingResult`; nothing about the source scenario changes as a result of calling it. Every
recommendation is advisory only — see [`GOVERNANCE.md`](GOVERNANCE.md).
