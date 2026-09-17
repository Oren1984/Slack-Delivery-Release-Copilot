from __future__ import annotations

from app.adapters.llm.base import ExplanationKind, LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """Default, offline, fully deterministic explanation adapter. Produces
    templated prose from the deterministic context it is given — no network
    access, no randomness, so output is reproducible for the same input.
    """

    def explain(self, kind: ExplanationKind, context: dict) -> str:
        if kind == "executive_summary":
            return self._executive_summary(context)
        if kind == "blocker_summary":
            return self._blocker_summary(context)
        if kind == "descoping_explanation":
            return self._descoping_explanation(context)
        if kind == "retrospective_draft":
            return self._retrospective_intro(context)
        raise ValueError(f"Unknown explanation kind: {kind}")

    def _executive_summary(self, ctx: dict) -> str:
        return (
            f"Release {ctx.get('version', '?')} for sprint '{ctx.get('sprint_name', '?')}' "
            f"is currently {ctx.get('gate_status', 'UNKNOWN')}. Convergence score is "
            f"{ctx.get('convergence_score', '?')}/100 ({ctx.get('risk_level', '?')} risk). "
            f"{len(ctx.get('blocking_reasons', []))} blocking issue(s) and "
            f"{len(ctx.get('warnings', []))} warning(s) were found. "
            f"Recommended next action: {ctx.get('recommended_next_action', 'review manually')}."
        )

    def _blocker_summary(self, ctx: dict) -> str:
        reasons = ctx.get("blocking_reasons", [])
        if not reasons:
            return "No blocking issues were found."
        bullet_list = "; ".join(reasons)
        return f"{len(reasons)} blocking issue(s) must be resolved before approval: {bullet_list}."

    def _descoping_explanation(self, ctx: dict) -> str:
        recs = ctx.get("recommendations", [])
        candidates = [r for r in recs if r.get("recommendation") == "Candidate for Descoping"]
        if not candidates:
            return "No descoping candidates were identified by the deterministic engine."
        titles = ", ".join(r.get("title", r.get("work_item_id", "?")) for r in candidates)
        return (
            f"{len(candidates)} item(s) are advisory descoping candidates to protect the "
            f"sprint goal: {titles}. This is a recommendation only; a human must accept or "
            "reject each item explicitly."
        )

    def _retrospective_intro(self, ctx: dict) -> str:
        return (
            f"Sprint '{ctx.get('sprint_id', '?')}' closed with a Say/Do Ratio of "
            f"{ctx.get('say_do_ratio', '?')}%. This draft summarizes deterministic findings for "
            "the team to discuss and refine together in the retrospective session."
        )
