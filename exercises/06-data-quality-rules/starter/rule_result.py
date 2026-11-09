"""Shared immutable DQ rule result used by checkers and the CLI runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "INDETERMINATE"]


@dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    status: Status
    severity: Literal["critical", "warning"]
    issues: list[dict[str, Any]] = field(default_factory=list)
