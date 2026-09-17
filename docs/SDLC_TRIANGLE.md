# The SDLC Triangle

This project is the third of three independent, runnable portfolio projects that together
illustrate governance across the full software delivery lifecycle. They are **not** an
integrated production platform — each is a standalone POC demonstrating a different phase, using
its own synthetic data and its own tool metaphor (ClickUp, Monday, Slack).

| Range | Project | Governance focus | Primary question it answers |
|---|---|---|---|
| 0–25% | ClickUp SDLC Risk Gatekeeper | Shift-left requirement quality | "Is this ready to start?" |
| 25–50% | Monday Smart PMO Agent | Sprint health & execution | "Are we on track, mid-sprint?" |
| **50–100%** | **Slack Delivery & Release Copilot** | Convergence, descoping, release governance, HITL approval, close-out | "Will we finish safely, and who says go?" |

## Why Three Separate Projects, Not One Platform

Each phase of the SDLC has a different governance question, a different set of stakeholders, and
a different cadence (requirement review is a one-time gate; sprint execution is continuous;
release governance is event-driven around sprint boundaries). Building one project per phase:

- keeps each individually understandable, runnable, and demonstrable without the others;
- avoids the complexity and maintenance cost of a unified schema/data model across phases that
  don't actually share a data source in most real organizations; and
- matches how these concerns are actually distributed across tools in most teams today.

## What This Project Covers (50–100%)

- **Sprint convergence** — is the team going to finish what it committed to?
- **Descoping** — if not, what should be advisory-cut to protect the sprint goal?
- **Release governance** — is the release candidate actually safe to ship?
- **Human approval** — an explicit, authorized, audited go/no-go decision.
- **Close-out** — what was actually delivered, and at what ratio to what was promised?
- **Retrospective** — what should the team discuss and improve next sprint?

## What This Project Does Not Cover

Anything upstream of "the sprint is mostly built": requirement intake quality (ClickUp project),
sprint planning and mid-sprint execution tracking (Monday project), or anything downstream of
"a human said go" — this project stops at recording the approval, and never executes a
deployment.
