"""Per-business-key diagnostics, independent from the checker algorithm."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

BusinessKey = tuple[str, int]
IssueCategory = Literal["missing", "extra", "changed", "duplicates", "malformed"]


@dataclass(frozen=True, slots=True)
class CheckIssue:
    """One finding: category and structured evidence for a business key."""

    category: IssueCategory
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TradeResult:
    """Issues accumulated for ONE known composite business key.

    Truly unkeyed malformed rows must be kept in a separate batch-level
    validation report, rather than assigned to an arbitrary trade.
    """

    business_key: BusinessKey
    issues: list[CheckIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def add_issue(self, category: IssueCategory, **details: Any) -> CheckIssue:
        issue = CheckIssue(category=category, details=details)
        self.issues.append(issue)
        return issue

    def issues_of(self, category: IssueCategory) -> list[CheckIssue]:
        return [issue for issue in self.issues if issue.category == category]
