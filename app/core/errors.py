from __future__ import annotations


class CopilotError(Exception):
    """Base class for all controlled application errors.

    Each carries an HTTP-status-appropriate code and a user-safe message.
    No CopilotError subclass may ever leak a stack trace or raw exception
    text to an API/UI caller.
    """

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ScenarioNotFoundError(CopilotError):
    status_code = 404


class ValidationFailedError(CopilotError):
    status_code = 422


class ReleaseNotFoundError(CopilotError):
    status_code = 404


class SprintNotFoundError(CopilotError):
    status_code = 404


class UnauthorizedDecisionError(CopilotError):
    status_code = 403


class InvalidReleaseTransitionError(CopilotError):
    status_code = 409


class DuplicateDecisionError(CopilotError):
    status_code = 409


class MissingEvidenceError(CopilotError):
    status_code = 409
