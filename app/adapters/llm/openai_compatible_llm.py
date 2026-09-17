from __future__ import annotations

import json

import httpx

from app.adapters.llm.base import ExplanationKind, LLMAdapter, LLMUnavailableError

SYSTEM_PROMPT = (
    "You rewrite already-finalized, deterministic release-governance findings into clear "
    "prose for a Slack audience. You must not invent facts, change any number or status, "
    "add missing evidence, or suggest an approval/hold decision. Only clarify wording."
)


class OpenAICompatibleLLMAdapter(LLMAdapter):
    """Optional, opt-in adapter for an OpenAI-compatible chat completions
    endpoint. Disabled unless LLM_MODE=openai_compatible and a base URL / key
    are explicitly configured. Any failure or invalid response raises
    LLMUnavailableError so the caller can fall back to the deterministic
    mock output — the workflow never blocks on this adapter.
    """

    def __init__(
        self, base_url: str, api_key: str, model: str, timeout_seconds: float = 8.0
    ) -> None:
        if not base_url or not api_key or not model:
            raise LLMUnavailableError("openai_compatible adapter is not fully configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds

    def explain(self, kind: ExplanationKind, context: dict) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"Explanation type: {kind}\nDeterministic findings "
                            f"(JSON, do not alter any value): {json.dumps(context, default=str)}",
                        },
                    ],
                    "temperature": 0.2,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailableError(f"openai_compatible call failed: {exc}") from exc

        if not isinstance(text, str) or not text.strip():
            raise LLMUnavailableError("openai_compatible adapter returned empty/invalid output.")
        return text.strip()
