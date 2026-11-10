"""Session 07: physical delivery counts can hide missing event IDs."""

import pytest

from data_qa.delivery_manifest import reconcile_delivery


def test_duplicate_hides_missing_when_total_counts_match() -> None:
    expected = ["E-1", "E-2"]
    actual = ["E-2", "E-2"]

    assert len(expected) == len(actual) == 2  # Misleading aggregate!
    report = reconcile_delivery(expected, actual, planned_count=2)

    assert report.missing == {"E-1"}
    assert report.unexpected == set()
    assert report.duplicates == {"E-2": 2}
    assert not report.passed


def test_equal_counts_and_distinct_counts_can_still_hide_wrong_ids() -> None:
    expected = ["E-1", "E-2"]
    actual = ["E-3", "E-4"]

    assert len(expected) == len(actual)
    assert len(set(expected)) == len(set(actual))

    report = reconcile_delivery(expected, actual, planned_count=2)

    assert report.missing == {"E-1", "E-2"}
    assert report.unexpected == {"E-3", "E-4"}
    assert report.duplicates == {}
    assert not report.passed


def test_exact_delivery_passes() -> None:
    report = reconcile_delivery(["E-1", "E-2"], ["E-2", "E-1"], planned_count=2)
    assert report.passed
    assert report.missing == report.unexpected == frozenset()
    assert report.duplicates == {}


def test_intentionally_empty_scenario_is_valid() -> None:
    report = reconcile_delivery([], [], planned_count=0)
    assert report.passed


def test_unexpectedly_empty_source_manifest_fails_setup() -> None:
    with pytest.raises(ValueError, match="planned 2"):
        reconcile_delivery([], [], planned_count=2)


def test_duplicate_source_ids_fail_manifest_validation() -> None:
    with pytest.raises(ValueError, match="duplicate event IDs"):
        reconcile_delivery(["E-1", "E-1"], ["E-1"], planned_count=2)


def test_unexpected_event_and_duplicate_are_separate_findings() -> None:
    report = reconcile_delivery(
        ["E-1", "E-2"],
        ["E-2", "E-2", "E-3"],
        planned_count=2,
    )
    assert report.missing == {"E-1"}
    assert report.unexpected == {"E-3"}
    assert report.duplicates == {"E-2": 2}
    assert not report.passed
