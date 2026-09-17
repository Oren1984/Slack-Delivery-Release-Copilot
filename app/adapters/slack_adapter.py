from __future__ import annotations

from app.core.logging import get_logger
from app.schemas.results import GateEvaluationResult

logger = get_logger(__name__)


def build_readiness_card_block_kit(
    *,
    release_id: str,
    version: str,
    sprint_name: str,
    gate: GateEvaluationResult,
    convergence_score: float,
    completed_count: int,
    planned_count: int,
    open_defect_summary: dict[str, int],
    qa_summary: str,
    dod_summary: str,
    rollback_ready: bool,
    audit_reference: str,
) -> dict:
    """Builds a Slack Block Kit-compatible JSON payload for the Release
    Readiness Card. This payload is never transmitted to a real Slack
    workspace by this adapter — see MockSlackAdapter.send().
    """
    defect_text = ", ".join(f"{k}: {v}" for k, v in open_defect_summary.items()) or "None open"
    blockers_text = "\n".join(f"- {r}" for r in gate.blocking_reasons) or "None"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Release Readiness: {version}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Sprint:*\n{sprint_name}"},
                    {"type": "mrkdwn", "text": f"*Gate status:*\n{gate.gate_status.value}"},
                    {"type": "mrkdwn", "text": f"*Convergence score:*\n{convergence_score}/100"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Completed vs planned:*\n{completed_count}/{planned_count}",
                    },
                    {"type": "mrkdwn", "text": f"*Open defects:*\n{defect_text}"},
                    {"type": "mrkdwn", "text": f"*QA:*\n{qa_summary}"},
                    {"type": "mrkdwn", "text": f"*Definition of Done:*\n{dod_summary}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Rollback ready:*\n{'Yes' if rollback_ready else 'No'}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Main blockers:*\n{blockers_text}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended action:*\n{gate.recommended_next_action}",
                },
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Audit reference: {audit_reference}"}],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve Deployment"},
                        "style": "primary",
                        "action_id": "approve_deployment",
                        "value": release_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Hold Release"},
                        "style": "danger",
                        "action_id": "hold_release",
                        "value": release_id,
                    },
                ],
            },
        ]
    }


class MockSlackAdapter:
    """Offline Slack adapter. `send` never performs a network call — it only
    logs and returns the payload for local preview, satisfying the
    "no real Slack message by default" requirement.
    """

    def send(self, channel: str, block_kit_payload: dict) -> dict:
        logger.info(f"[mock-slack] would post to channel={channel} (offline preview only)")
        return {"ok": True, "channel": channel, "delivered": False, "payload": block_kit_payload}
