from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

ExplanationKind = Literal[
    "executive_summary",
    "blocker_summary",
    "descoping_explanation",
    "retrospective_draft",
]


class LLMUnavailableError(Exception):
    """Raised by an LLM adapter when it cannot produce a valid explanation.
    The caller must fall back to deterministic/mock output and continue —
    this error must never propagate to the API/UI layer or block a
    deterministic result.
    """


@dataclass
class LLMExplanation:
    text: str
    used_fallback: bool


class LLMAdapter(ABC):
    """Explanation-only interface. Implementations may ONLY rewrite,
    summarize, or explain deterministic findings supplied in `context`.
    They must never be asked to produce or alter a calculated value, gate
    status, or approval decision — those are always passed in as already-
    final facts.
    """

    @abstractmethod
    def explain(self, kind: ExplanationKind, context: dict) -> str:
        """Returns explanatory text. Raises LLMUnavailableError on any
        failure or invalid-output condition instead of returning malformed
        text."""
        raise NotImplementedError
