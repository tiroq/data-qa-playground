"""Session 05 starter tests. These intentionally fail until implemented."""

from copy import deepcopy

import pytest

from data_qa.reconciliation import compare_events

CATEGORIES = ("missing", "extra", "changed", "duplicates", "malformed")


def event(
    trade_id: str = "T1",
    account_id: int = 100,
    version: int = 1,
    event_id: str = "E1",
    status: str = "CLOSED",
    pnl: str | None = "10.00",
) -> dict:
    return {
        "trade_id": trade_id,
        "account_id": account_id,
        "version": version,
        "event_id": event_id,
        "status": status,
        "pnl": pnl,
    }


def expected(**overrides: int) -> dict[str, int]:
    return {name: overrides.get(name, 0) for name in CATEGORIES}


@pytest.mark.parametrize(
    ("source", "target", "counts"),
    [
        pytest.param([], [], expected(), id="empty-sets"),
        pytest.param([event()], [], expected(missing=1), id="missing-trade"),
        pytest.param([], [event()], expected(extra=1), id="extra-trade"),
        pytest.param(
            [event(pnl="10.01")],
            [event(pnl="10.00")],
            expected(changed=1),
            id="changed-pnl",
        ),
        pytest.param(
            [event(), event(version=2, event_id="E2", pnl="15.00")],
            [event()],
            expected(changed=1),
            id="stale-target-version",
        ),
        pytest.param(
            [event(), event()],
            [event()],
            expected(duplicates=1),
            id="duplicate-delivery-in-source",
        ),
        pytest.param(
            [{"trade_id": "T1", "version": 1, "event_id": "E1", "status": "OPEN", "pnl": "0"}],
            [],
            expected(malformed=1),
            id="missing-account-key",
        ),
        pytest.param(
            [event(account_id=None)],
            [],
            expected(malformed=1),
            id="nullable-account-key",
        ),
        pytest.param(
            [event(pnl="10000000000000000.01")],
            [event(pnl="10000000000000000.02")],
            expected(changed=1),
            id="decimal-precision",
        ),
    ],
)
def test_comparison_categories(source: list[dict], target: list[dict], counts: dict[str, int]) -> None:
    report = compare_events(source, target)
    assert set(report) == set(CATEGORIES)
    assert {name: len(report[name]) for name in CATEGORIES} == counts


def test_does_not_mutate_inputs() -> None:
    source = [event(), event(version=2, event_id="E2")]
    target = [event()]
    source_before, target_before = deepcopy(source), deepcopy(target)

    compare_events(source, target)

    assert source == source_before
    assert target == target_before


def test_order_independent_report() -> None:
    source = [
        event(trade_id="T2", event_id="E2"),
        event(trade_id="T1", event_id="E1"),
        event(trade_id="T1", event_id="E1"),
    ]
    target = [event(trade_id="T3", event_id="E3")]

    first = compare_events(source, target)
    reversed_input = compare_events(list(reversed(source)), list(reversed(target)))

    assert first == reversed_input

def test_multiple_business_keys_have_separate_issue_records() -> None:
    """A batch-wide boolean would lose which trade failed."""
    source = [
        event(trade_id="T1", event_id="E1", pnl="15.50"),
        event(trade_id="T2", event_id="E2"),
    ]
    target = [
        event(trade_id="T1", event_id="E1", pnl="15.00"),
        event(trade_id="T3", event_id="E3"),
    ]

    report = compare_events(source, target)

    assert {(x["trade_id"], x["account_id"]) for x in report["missing"]} == {("T2", 100)}
    assert {(x["trade_id"], x["account_id"]) for x in report["extra"]} == {("T3", 100)}
    assert {(x["trade_id"], x["account_id"]) for x in report["changed"]} == {("T1", 100)}
    for category in CATEGORIES:
        for issue in report[category]:
            assert set(issue) == {"trade_id", "account_id", "details"}
            assert isinstance(issue["details"], dict)
