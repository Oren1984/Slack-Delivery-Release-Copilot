from __future__ import annotations

from enum import StrEnum


class Priority(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class BusinessValue(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class WorkItemStatus(StrEnum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    IN_CODE_REVIEW = "In Code Review"
    IN_QA = "In QA"
    DONE = "Done"
    BLOCKED = "Blocked"


class CodeReviewStatus(StrEnum):
    NOT_STARTED = "Not Started"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    CHANGES_REQUESTED = "Changes Requested"


class QAStatus(StrEnum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    PASSED = "Passed"
    FAILED = "Failed"


class DefectSeverity(StrEnum):
    BLOCKER = "Blocker"
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class DefectStatus(StrEnum):
    OPEN = "Open"
    CLOSED = "Closed"


class FinalDisposition(StrEnum):
    """Human-recorded outcome for a committed work item at sprint end.

    Set by whoever owns the sprint data (never inferred or changed by the
    system itself) to reflect what people actually decided, including
    whether an advisory descoping recommendation was accepted.
    """

    PENDING = "Pending"
    DELIVERED = "Delivered"
    DESCOPED = "Descoped"
    CARRIED_OVER = "Carried Over"


class Role(StrEnum):
    DELIVERY_MANAGER = "Delivery Manager"
    TECH_LEAD = "Tech Lead"
    QA_LEAD = "QA Lead"
    OBSERVER = "Observer"


class RiskLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DescopingRecommendation(StrEnum):
    PROTECT = "Protect"
    CANDIDATE_FOR_DESCOPING = "Candidate for Descoping"
    MUST_HOLD = "Must Hold"
    COMPLETED = "Completed"
    NEEDS_HUMAN_REVIEW = "Needs Human Review"


class GateStatus(StrEnum):
    READY_FOR_HUMAN_APPROVAL = "READY_FOR_HUMAN_APPROVAL"
    NOT_READY = "NOT_READY"
    HOLD_REQUIRED = "HOLD_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DecisionType(StrEnum):
    APPROVED = "APPROVED"
    HELD = "HELD"
