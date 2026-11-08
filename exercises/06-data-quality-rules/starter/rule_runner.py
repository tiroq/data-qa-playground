"""Session 06: input loader and intentionally incomplete DQ evaluator.

Run from repository root:
  python exercises/06-data-quality-rules/starter/rule_runner.py \
    exercises/06-data-quality-rules/fixtures/dq_batches.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "INDETERMINATE"]


@dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    status: Status
    severity: Literal["critical", "warning"]
    issues: list[dict[str, Any]] = field(default_factory=list)


def load_cohorts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported fixture schema")
    cohorts = payload.get("cohorts")
    if not isinstance(cohorts, list):
        raise ValueError("cohorts must be a list")
    return cohorts


def evaluate_rules(cohort: dict[str, Any]) -> list[RuleOutcome]:
    """TODO (learner): implement the rules and thresholds from CONTRACT.md."""
    raise NotImplementedError("Session 06: rule evaluation is your live-coding task")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python rule_runner.py <dq_batches.json>")
    for batch in load_cohorts(Path(sys.argv[1])):
        print(f'{batch["name"]}: physical_rows={len(batch["records"])} expected_events={batch["expected_events"]}')
    print("Fixture ready. Rule evaluation is intentionally not implemented.")
