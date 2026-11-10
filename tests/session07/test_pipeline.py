"""Starter contract tests for the Session 07 fake pipeline.

These tests do not exercise a real HTTP API, PostgreSQL, or ClickHouse.
Extend them during the interview exercise; do not treat a passing fake as E2E.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "exercises/07-pytest-architecture/fixtures/api_cases.json"


def _load_cases() -> list[dict[str, Any]]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
    if not cases:
        raise ValueError("Session 07 case matrix must not be empty")
    return cases


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["name"])
def test_pipeline_case(pipeline: Any, case: dict[str, Any]) -> None:
    """Physical submissions, processing outcome, and target rows must agree."""
    assert pipeline.source == []
    assert pipeline.target == []

    for event in case["payloads"]:
        assert pipeline.submit(event) == event["event_id"]

    assert pipeline.source == case["payloads"]
    assert len(pipeline.source) == case["expected_source"]
    assert pipeline.target == [], "Processing should not occur before drain()"

    pipeline.fail_processing = case["fail_processing"]
    if case["fail_processing"]:
        with pytest.raises(RuntimeError, match="synthetic processing failure"):
            pipeline.drain()
    else:
        assert pipeline.drain() == len(case["payloads"])

    assert len(pipeline.target) == case["expected_target"]
    if not case["fail_processing"]:
        # Lists preserve physical duplicates; equal event IDs are not deduplicated.
        assert pipeline.target == case["payloads"]

    if case["expected_target"] > 0:
        assert pipeline.target, "Unexpected empty target: processing was required"


def test_unprocessed_event_does_not_count_as_success(pipeline: Any) -> None:
    """Negative control: the required target-data assertion must fail pre-drain."""
    pipeline.submit({"event_id": "NEG-1", "trade_id": "T-1", "account_id": "A1"})
    assert len(pipeline.source) == 1
    with pytest.raises(AssertionError, match="Expected processed data"):
        assert pipeline.target, "Expected processed data, got zero target rows"


def test_missing_event_id_is_rejected(pipeline: Any) -> None:
    with pytest.raises(ValueError, match="event_id is required"):
        pipeline.submit({"trade_id": "T-1", "account_id": "A1"})
    assert pipeline.source == []
    assert pipeline.target == []
