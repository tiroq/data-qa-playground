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



def test_three_identical_deliveries_report_one_duplicate_with_counts() -> None:
    row = event()
    report = compare_events([row, row, row], [row])
    assert len(report["duplicates"]) == 1
    details = report["duplicates"][0]["details"]
    assert details["event_id"] == "E1"
    assert details["side"] == "source"
    assert details["delivery_count"] == 3
    assert details["duplicate_count"] == 2
    assert report["changed"] == []


def test_same_event_and_version_with_conflicting_payload_is_changed() -> None:
    initial = event(pnl="8.0000")
    conflict = event(pnl="8.5000")
    report = compare_events([initial, conflict], [initial])
    assert report["duplicates"] == []
    assert len(report["changed"]) == 1
    details = report["changed"][0]["details"]
    assert details["reason"] == "payload_conflict"
    assert details["event_id"] == "E1"
    assert details["side"] == "source"


def test_decimal_scale_is_semantically_equivalent_in_replayed_events() -> None:
    first = event(pnl="7.00")
    same_amount = event(pnl="7.0000")
    report = compare_events([first, same_amount], [first])
    assert report["changed"] == []
    assert len(report["duplicates"]) == 1


def test_different_event_ids_are_not_transport_duplicates() -> None:
    first = event(event_id="E1")
    second = event(event_id="E2")
    report = compare_events([first, second], [first])
    assert report["duplicates"] == []
    assert report["changed"] == []


def test_invalid_keyed_row_quarantines_key_to_avoid_false_extra() -> None:
    invalid = event(version=0)
    report = compare_events([invalid], [event()])
    assert len(report["malformed"]) == 1
    assert report["malformed"][0]["details"]["side"] == "source"
    assert report["extra"] == []
    assert report["missing"] == []


@pytest.mark.parametrize("invalid_pnl", ["NaN", "Infinity", "n/a", 1.25, True])
def test_invalid_pnl_is_malformed(invalid_pnl: object) -> None:
    report = compare_events([event(pnl=invalid_pnl)], [])
    assert len(report["malformed"]) == 1
    assert "pnl" in report["malformed"][0]["details"]["reason"]
    assert report["missing"] == []


def test_nullable_pnl_can_be_preserved_for_future_status_policy() -> None:
    row = event(status="NEW", pnl=None)
    assert compare_events([row], [row]) == {
        "missing": [], "extra": [], "changed": [], "duplicates": [], "malformed": [],
    }


def test_invalid_row_evidence_is_copied_not_mutated() -> None:
    row = event(version=0)
    report = compare_events([row], [])
    row["version"] = 999
    assert report["malformed"][0]["details"]["row"]["version"] == 0


def test_malformed_and_mixed_input_report_is_order_independent() -> None:
    invalid_keyed = event(trade_id="T3", version=0)
    invalid_unkeyed = {"trade_id": None, "account_id": 100, "version": 1}
    source = [
        event(trade_id="T2", event_id="E2"),
        invalid_keyed,
        event(trade_id="T1", event_id="E1"),
        event(trade_id="T1", event_id="E1"),
        invalid_unkeyed,
    ]
    target = [event(trade_id="T3", event_id="E3")]
    assert compare_events(source, target) == compare_events(
        list(reversed(source)), list(reversed(target))
    )



def _coverage_for(
    detailed: dict, trade_id: str = "T1", account_id: int = 100
) -> dict[str, str]:
    entries = [
        entry["checks"] for entry in detailed["coverage"]["business_keys"]
        if entry["trade_id"] == trade_id and entry["account_id"] == account_id
    ]
    assert len(entries) == 1
    return entries[0]


def test_best_effort_keeps_duplicate_evidence_when_version_is_unknown() -> None:
    from data_qa.reconciliation import compare_events_detailed

    valid = event(version=2, event_id="E2", pnl="7.00")
    invalid = event(version=None, event_id="E3", pnl="8.00")
    detailed = compare_events_detailed([valid, valid, invalid], [valid])
    report = detailed["report"]
    assert len(report["duplicates"]) == 1
    assert report["duplicates"][0]["details"]["duplicate_count"] == 1
    assert len(report["malformed"]) == 1
    assert report["changed"] == []

    coverage = _coverage_for(detailed)
    assert coverage["presence"] == "complete"
    assert coverage["duplicates"] == "partial"
    assert coverage["payload_conflict"] == "partial"
    assert coverage["version_mismatch"] == "blocked"
    assert coverage["state_mismatch"] == "blocked"


def test_known_old_malformed_version_does_not_block_latest_comparison() -> None:
    from data_qa.reconciliation import compare_events_detailed

    malformed_old = event(version=1, event_id="E1", status=None)
    valid_new = event(version=2, event_id="E2", pnl="9.00")
    target_old = event(version=1, event_id="T1", pnl="5.00")
    detailed = compare_events_detailed([malformed_old, valid_new], [target_old])
    report = detailed["report"]
    reasons = {row["details"].get("reason") for row in report["changed"]}
    assert reasons == {"version_mismatch"}
    assert len(report["malformed"]) == 1
    coverage = _coverage_for(detailed)
    assert coverage["version_mismatch"] == "complete"
    assert coverage["duplicates"] == "partial"


def test_malformed_latest_payload_blocks_state_mismatch_but_not_validation() -> None:
    from data_qa.reconciliation import compare_events_detailed

    bad_latest = event(version=2, event_id="E3", pnl="not-numeric")
    valid_source = event(version=2, event_id="E2", pnl="7.00")
    valid_target = event(version=2, event_id="T2", pnl="8.00")
    detailed = compare_events_detailed(
        [bad_latest, valid_source], [valid_target]
    )
    assert len(detailed["report"]["malformed"]) == 1
    assert detailed["report"]["changed"] == []
    assert _coverage_for(detailed)["state_mismatch"] == "blocked"


def test_unkeyed_malformed_target_suppresses_only_plausible_missing() -> None:
    from data_qa.reconciliation import compare_events_detailed

    source = [
        event(trade_id="T1", account_id=100),
        event(trade_id="T2", account_id=100, event_id="E2"),
    ]
    bad_target = event(trade_id="T1", account_id=None)
    detailed = compare_events_detailed(source, [bad_target])
    report = detailed["report"]
    assert {(row["trade_id"], row["account_id"]) for row in report["missing"]} == {
        ("T2", 100)
    }
    assert _coverage_for(detailed, "T1")["presence"] == "blocked"
    assert _coverage_for(detailed, "T2")["presence"] == "complete"
    assert detailed["coverage"]["unkeyed_malformed_count"] == 1


def test_partial_account_identity_only_impacts_matching_account() -> None:
    from data_qa.reconciliation import compare_events_detailed

    source = [
        event(trade_id="T1", account_id=100),
        event(trade_id="T2", account_id=200, event_id="E2"),
    ]
    bad_target = event(trade_id=None, account_id=100)
    detailed = compare_events_detailed(source, [bad_target])
    assert [row["trade_id"] for row in detailed["report"]["missing"]] == ["T2"]
    assert _coverage_for(detailed, "T1", 100)["presence"] == "blocked"
    assert _coverage_for(detailed, "T2", 200)["presence"] == "complete"


def test_malformed_source_does_not_create_false_extra_on_same_key() -> None:
    from data_qa.reconciliation import compare_events_detailed

    detailed = compare_events_detailed([event(version=0)], [event()])
    report = detailed["report"]
    assert report["extra"] == []
    assert len(report["malformed"]) == 1
    assert _coverage_for(detailed)["presence"] == "blocked"


def test_valid_payload_conflict_survives_unrelated_malformed_same_key() -> None:
    from data_qa.reconciliation import compare_events_detailed

    valid = event(version=2, event_id="E2", pnl="8.00")
    conflicting = event(version=2, event_id="E2", pnl="9.00")
    bad_old = event(version=1, event_id="E1", status=None)
    detailed = compare_events_detailed([valid, conflicting, bad_old], [valid])
    reasons = [row["details"].get("reason") for row in detailed["report"]["changed"]]
    assert reasons == ["payload_conflict"]
    assert _coverage_for(detailed)["payload_conflict"] == "partial"
    assert _coverage_for(detailed)["version_mismatch"] == "blocked"


def test_malformed_only_key_gets_blocked_coverage_without_running_empty_group() -> None:
    from data_qa.reconciliation import compare_events_detailed

    detailed = compare_events_detailed([event(version=None)], [])
    assert len(detailed["report"]["malformed"]) == 1
    assert detailed["report"]["missing"] == []
    coverage = _coverage_for(detailed)
    assert coverage["presence"] == "blocked"
    assert coverage["duplicates"] == "blocked"
    assert coverage["state_mismatch"] == "blocked"


def test_detailed_result_is_order_independent_and_preserves_old_api() -> None:
    from data_qa.reconciliation import compare_events_detailed

    source = [
        event(event_id="E2", version=2),
        event(version=None, event_id="E3"),
        event(event_id="E2", version=2),
        event(trade_id="T2", event_id="E1"),
    ]
    target = [
        event(event_id="E2", version=2),
        event(trade_id="T3", event_id="E9"),
    ]
    first = compare_events_detailed(source, target)
    second = compare_events_detailed(list(reversed(source)), list(reversed(target)))
    assert first == second
    assert compare_events(source, target) == first["report"]
    assert set(first["report"]) == set(CATEGORIES)
