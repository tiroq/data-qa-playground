"""Offline negative-control checks for the streaming lab.

These are unit tests for DQ logic and synthetic fixtures, NOT proof that the
actual Kafka/Flink/ClickHouse pipeline ran. The E2E workflow is separate.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from streaming_lab.fixtures import make_fixture, render_sql, validate_run_id
from streaming_lab.gate import inspect

BASE = 1_796_000_000_000


def example(scenario: str, *, omit: str | None = None):
    expected, published = make_fixture("test-run", scenario, base_time_ms=BASE)
    if omit is not None:
        published = [row for row in published if row["event_id"] != omit]
    actual = [
        {
            **row,
            "available_at": datetime.fromtimestamp(
                (row["event_time_ms"] + 1000) / 1000, tz=timezone.utc
            ).isoformat(),
        }
        for row in published
    ]
    manifest = {"run_id": "test-run", "scenario": scenario,
                "planned_events": len(expected), "sealed": True}
    return manifest, expected, actual


def rules(report: dict) -> set[str]:
    return {item["rule"] for item in report["issues"]}


def test_healthy_cohort_is_verified() -> None:
    report = inspect(*example("healthy"), now_ms=BASE + 2000)
    assert report["status"] == "PASS"
    assert report["sla"]["status"] == "PASS"
    assert report["expected_count"] == 6
    assert report["distinct_actual_events"] == 6


def test_exact_redelivery_is_a_warning_not_double_business_effect() -> None:
    report = inspect(*example("duplicate"), now_ms=BASE + 2000)
    assert report["status"] == "PASS"
    assert report["actual_physical_count"] == 7
    assert report["distinct_actual_events"] == 6
    assert {w["rule"] for w in report["warnings"]} == {"DQ-REDELIVERY"}


@pytest.mark.parametrize(("scenario", "expected_rule"), [
    ("missing", "DQ-MISSING"),
    ("corrupt", "DQ-PAYLOAD"),
    ("extra", "DQ-UNEXPECTED"),
    ("conflict", "DQ-SAME-VERSION"),
])
def test_negative_scenarios_actually_fail(scenario: str, expected_rule: str) -> None:
    report = inspect(*example(scenario), now_ms=BASE + 2000)
    assert report["status"] == "FAIL"
    assert expected_rule in rules(report)


def test_late_older_business_version_does_not_change_identity_counts() -> None:
    report = inspect(*example("out_of_order"), now_ms=BASE + 2000)
    assert report["status"] == "PASS"
    assert report["distinct_actual_events"] == 6


def test_physical_count_can_equal_expected_with_missing_and_duplicate() -> None:
    manifest, expected, actual = example("healthy")
    actual = [row for row in actual if row["event_id"] != "E004"]
    actual.append(dict(actual[1]))
    assert len(expected) == len(actual) == 6
    report = inspect(manifest, expected, actual, now_ms=BASE + 2000)
    assert report["status"] == "FAIL"
    assert "DQ-MISSING" in rules(report)
    assert any(w["rule"] == "DQ-REDELIVERY" for w in report["warnings"])


def test_immutable_event_id_payload_conflict_is_separate() -> None:
    manifest, expected, actual = example("duplicate")
    actual[-1]["pnl"] = "999.00"
    report = inspect(manifest, expected, actual, now_ms=BASE + 2000)
    assert {"DQ-EVENT-CONFLICT", "DQ-PAYLOAD"} <= rules(report)


def test_empty_source_cannot_be_vacuously_green() -> None:
    manifest = {"run_id": "test-run", "scenario": "empty",
                "planned_events": 0, "sealed": True}
    report = inspect(manifest, [], [], now_ms=BASE)
    assert report["status"] == "FAIL"
    assert "DQ-EMPTY" in rules(report)


def test_manifest_missing_or_unsealed_never_passes() -> None:
    manifest, expected, actual = example("healthy")
    assert inspect(None, expected, actual, now_ms=BASE)["status"] == "INDETERMINATE"
    manifest["sealed"] = False
    assert inspect(manifest, expected, actual, now_ms=BASE)["status"] == "INDETERMINATE"


def test_source_manifest_count_mismatch_is_blocking() -> None:
    manifest, expected, actual = example("healthy")
    manifest["planned_events"] = 8
    report = inspect(manifest, expected, actual, now_ms=BASE)
    assert report["status"] == "FAIL"
    assert "DQ-MANIFEST" in rules(report)


def test_sla_is_distinct_from_event_integrity() -> None:
    manifest, expected, actual = example("healthy")
    for row in actual:
        event_ts = row["event_time_ms"] + 11 * 60 * 1000
        row["available_at"] = datetime.fromtimestamp(
            event_ts / 1000, tz=timezone.utc
        ).isoformat()
    report = inspect(manifest, expected, actual, now_ms=BASE + 12 * 60 * 1000)
    assert "DQ-SLA" in rules(report)
    assert report["sla"]["status"] == "FAIL"
    assert "DQ-MISSING" not in rules(report)


def test_generated_postgres_sql_is_manifest_first_and_seal_separate() -> None:
    expected, published = make_fixture("test-run", "missing", base_time_ms=BASE)
    sql, seal = render_sql("test-run", "missing", expected)
    assert "BEGIN;" in sql and "COMMIT;" in sql
    assert "sealed" in sql
    assert "SET sealed = TRUE" not in sql
    assert "SET sealed = TRUE" in seal
    assert len(expected) == 6 and len(published) == 5


@pytest.mark.parametrize("bad", ["", "has space", "bad'quote", "x" * 49, "../bad"])
def test_run_id_validation_rejects_unsafe_identifiers(bad: str) -> None:
    with pytest.raises(ValueError):
        validate_run_id(bad)


def test_run_id_validation_accepts_ci_ids() -> None:
    assert validate_run_id("ci-123_45") == "ci-123_45"
