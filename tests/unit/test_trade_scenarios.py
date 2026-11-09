"""Session 05 TDD scenarios, grounded in the repository's synthetic trading fixtures.

The Session 04 source/target snapshots are used for business-key presence tests.
The Session 02 versioned fixture is used for latest-version/PnL tests.
These are NOT Exness production data, and have different schema/field names
from Record; see the exercise notes for the explicit test-only projection.

Existing tests remain unchanged. Cases for missing implementations are strict
xfail: when they start passing, remove the mark and keep the assertion.
"""

from __future__ import annotations

import pytest

from data_qa.checkers.base import data_checkers, AbstractChecker
from data_qa.data.base import Record
from data_qa.data.trade_group import (
    AmbiguousLatestVersionError,
    EmptyTradeGroupError,
    Side,
    TradeGroup,
)
from data_qa.reconciliation import compare_events


# Direct transcription of (physical_id, trade_id, account_id, version) from
# exercises/04-reconciliation/sql/01-fixture.sql. Rows with NULL business
# identity are intentionally excluded HERE and tested independently below.
LAB04_SOURCE = [
    (1, 101, "A1", 1),
    (2, 101, "A1", 1),
    (3, 102, "A1", 1),
    (4, 103, "A2", 2),
    (5, 105, "A3", 1),
    (6, 106, "A3", 1),
    (7, 107, "A4", 1),
    (8, 108, "A5", 2),
    (9, 108, "A5", 3),
    (10, 109, "A5", 3),
    (11, 110, "A6", 2),
    (12, 111, "A6", 3),
    (13, 112, "A7", 3),
    (14, 113, "A7", 2),
    (15, 113, "A7", 3),
]
LAB04_TARGET = [
    (11, 101, "A1", 1),
    (12, 101, "A1", 1),
    (13, 103, "A2", 2),
    (14, 104, "A2", 1),
    (15, 105, "A3", 1),
    (16, 106, "A3", 1),
    (17, 107, "A4", 1),
    (19, 108, "A5", 2),
    (20, 109, "A5", 3),
    (21, 110, "A6", 3),
    (22, 111, "A6", 3),
    (23, 111, "A6", 3),
    (24, 112, "A7", 2),
    (25, 112, "A7", 2),
    (26, 112, "A7", 3),
    (27, 113, "A7", 3),
    (29, 115, "A8", 1),
]

# (ingest_id, trade_id, account_id, version, status, pnl), transcribed
# from postgres/fixtures/02-trade-versions.sql (same logical rows as ClickHouse).
LAB02_VERSIONS = [
    (1, 201, "A1", 1, "NEW", "5.0000"),
    (2, 201, "A1", 2, "FILLED", "7.0000"),
    (3, 201, "A1", 2, "FILLED", "7.0000"),
    (4, 202, "A1", 1, "NEW", "-2.5000"),
    (5, 202, "A1", 2, "FILLED", "-1.5000"),
    (6, 203, "A2", 2, "FILLED", "9.0000"),
    (7, 203, "A2", 1, "NEW", "1.0000"),  # late-arriving older version
    (8, 204, "A2", 1, None, None),
    (9, 205, "A3", 1, "NEW", "4.0000"),
    (10, 205, "A3", 2, "FILLED", "8.0000"),
    (11, 205, "A3", 2, "FILLED", "8.5000"),  # conflicting v2
    (12, 206, "A3", 1, "CANCELLED", "0.0000"),
]


def fixture_key(trade_id: int, account_id: str) -> tuple[str, int]:
    """Test-only, reversible for this fixture: SQL (201,'A1') -> ('T201',1).

    Record currently declares (str,int), whereas SQL declares (BIGINT,TEXT).
    Never use this conversion as a production identity contract.
    """
    assert account_id.startswith("A") and account_id[1:].isdigit()
    return f"T{trade_id}", int(account_id[1:])


def lab04_groups() -> list[TradeGroup]:
    groups: dict[tuple[str, int], TradeGroup] = {}
    for side, rows in (("source", LAB04_SOURCE), ("target", LAB04_TARGET)):
        for row_id, trade_id, account_id, version in rows:
            key = fixture_key(trade_id, account_id)
            group = groups.setdefault(key, TradeGroup(business_key=key))
            # Session 04 has "amount", NOT pnl, and source has no status:
            # these are identity-only projections. Do not fake a pnl mapping.
            record = Record(
                trade_id=key[0],
                account_id=key[1],
                version=version,
                event_id=f"{side}-{row_id}",
            )
            getattr(group, f"add_{side}")(record)
    return [groups[key] for key in sorted(groups)]


def lab02_group(trade_id: int) -> TradeGroup:
    rows = [row for row in LAB02_VERSIONS if row[1] == trade_id]
    if not rows:
        raise ValueError(f"No fixture for trade_id={trade_id}")
    key = fixture_key(trade_id, rows[0][2])
    source = [
        Record(
            trade_id=key[0],
            account_id=key[1],
            version=version,
            event_id=f"ingest-{ingest_id}",
            status=status,
            pnl=pnl,
        )
        for ingest_id, _, _, version, status, pnl in rows
    ]
    return TradeGroup(business_key=key, source=source)


def presence_chain() -> AbstractChecker:
    """Currently implemented checkers; add new ones here when available."""
    return data_checkers  # type: ignore[return-value]


def issues(group: TradeGroup) -> list[str]:
    return [issue.category for issue in group.run_checks(presence_chain()).issues]


def test_lab04_fixture_identity_and_cardinality() -> None:
    groups = lab04_groups()
    assert len(groups) == 14  # union of valid business keys
    assert sum(len(g.source) for g in groups) == 15
    assert sum(len(g.target) for g in groups) == 17
    assert {g.business_key for g in groups} == {
        ("T101", 1),
        ("T102", 1),
        ("T103", 2),
        ("T104", 2),
        ("T105", 3),
        ("T106", 3),
        ("T107", 4),
        ("T108", 5),
        ("T109", 5),
        ("T110", 6),
        ("T111", 6),
        ("T112", 7),
        ("T113", 7),
        ("T115", 8),
    }


def test_lab04_missing_and_extra_match_snapshot() -> None:
    reports = {group.business_key: issues(group) for group in lab04_groups()}
    anomalies = {key: categories for key, categories in reports.items() if categories}

    assert anomalies == {
        ("T102", 1): ["missing"],  # source row 3, absent in target
        ("T104", 2): ["extra"],  # target record 14, absent in source
        ("T115", 8): ["extra"],  # target record 29, absent in source
    }


@pytest.mark.parametrize(
    ("source_count", "target_count", "expected"),
    [
        (1, 0, ["missing"]),
        (0, 1, ["extra"]),
        (1, 1, []),
    ],
)
def test_presence_truth_table(
    source_count: int, target_count: int, expected: list[str]
) -> None:
    key = ("T999", 9)
    group = TradeGroup(
        business_key=key,
        source=[Record(trade_id=key[0], account_id=key[1], event_id="src-1")]
        * source_count,
        target=[Record(trade_id=key[0], account_id=key[1], event_id="tgt-1")]
        * target_count,
    )
    print(
        f"source_count={source_count}, target_count={target_count}, expected={expected}"
    )
    print(f"Group: {group}")
    print(f"Checker chain:")
    checker = presence_chain()
    while checker:
        print(f"- {checker.__class__.__name__}")
        checker = checker._next_handler
    print(f"Result: {group.run_checks(presence_chain())}")
    assert issues(group) == expected


def test_empty_trade_group_raises_with_business_key() -> None:
    """Two empty sides violate the group invariant when checks begin."""
    key = ("T999", 9)
    group = TradeGroup(business_key=key)

    with pytest.raises(EmptyTradeGroupError, match="has no records") as error:
        group.run_checks(presence_chain())

    assert repr(key) in str(error.value)


# @pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="TradeGroup.latest() is the learner's TODO")
@pytest.mark.parametrize(
    ("trade_id", "version", "status", "pnl"),
    [
        (201, 2, "FILLED", "7.0000"),  # same-version identical payload twice
        (202, 2, "FILLED", "-1.5000"),
        (203, 2, "FILLED", "9.0000"),  # v1 ingested after v2
        (206, 1, "CANCELLED", "0.0000"),
    ],
)
def test_lab02_latest_version(
    trade_id: int, version: int, status: str, pnl: str
) -> None:
    selected = lab02_group(trade_id).latest(Side.SOURCE)
    assert selected is not None
    assert (selected.version, selected.status, selected.pnl) == (version, status, pnl)


# @pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Need an explicit same-max-version conflict policy")
def test_lab02_conflicting_latest_version_must_not_win_arbitrarily() -> None:
    # lab02 205/A3: two physical v2 rows, pnl=8.0000 and pnl=8.5000.
    # This test chooses ValueError as a proposed policy. Change it explicitly
    # if the checker will instead record an ambiguity in TradeResult.
    with pytest.raises(AmbiguousLatestVersionError, match="(?i)conflict|ambig"):
        lab02_group(205).latest(Side.SOURCE)


# @pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Latest() must define empty-side behavior")
def test_latest_on_empty_side_is_none() -> None:
    print(lab02_group(201).latest(Side.TARGET))
    assert lab02_group(201).latest(Side.TARGET) is None


# @pytest.mark.xfail(strict=True, raises=AssertionError, reason="Wire a Changed checker into presence_chain()")
@pytest.mark.parametrize(
    ("source_version", "target_version", "source_pnl", "target_pnl"),
    [
        (2, 1, "7.0000", "5.0000"),  # target is stale, not trade-level missing
        (2, 2, "7.0000", "7.0001"),  # exact Decimal difference
        (2, 2, "10000000000000000.01", "10000000000000000.02"),
    ],
)
def test_latest_state_difference_reported_as_changed(
    source_version: int, target_version: int, source_pnl: str, target_pnl: str
) -> None:
    group = TradeGroup(
        business_key=("T201", 1),
        source=[Record("T201", 1, source_version, "S2", "FILLED", source_pnl)],
        target=[Record("T201", 1, target_version, "T2", "FILLED", target_pnl)],
    )
    assert "changed" in issues(group)
    assert "missing" not in issues(group)


# @pytest.mark.xfail(strict=True, raises=AssertionError, reason="Wire a Duplicate checker into presence_chain()")
def test_same_event_replayed_on_source_is_a_transport_duplicate() -> None:
    row = Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")
    group = TradeGroup(
        ("T201", 1),
        source=[row, Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")],
        target=[row],
    )
    report = group.run_checks(presence_chain())
    print(group)
    print(report)
    assert len(report.issues_of("duplicates")) == 1
    assert report.issues_of("duplicates")[0].details["side"] == "source"
    assert report.issues_of("duplicates")[0].details["event_id"] == "E201V2"


# @pytest.mark.xfail(strict=True, raises=AssertionError, reason="Missing and duplicate must be independent issues")
def test_missing_trade_can_also_have_duplicate_delivery() -> None:
    record = Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")
    group = TradeGroup(("T201", 1), source=[record, record], target=[])
    assert set(issues(group)) == {"missing", "duplicates"}


def test_distinct_lifecycle_versions_not_flagged_as_presence_errors() -> None:
    group = TradeGroup(
        ("T201", 1),
        source=[
            Record("T201", 1, 1, "E201V1", "NEW", "5.0000"),
            Record("T201", 1, 2, "E201V2", "FILLED", "7.0000"),
        ],
        target=[Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")],
    )
    # This guards only the *existing* presence handlers; version/replay checks
    # will be asserted separately after those implementations are wired.
    assert issues(group) == []


# @pytest.mark.xfail(strict=True, raises=AssertionError, reason="Conflict detection is not implemented yet")
def test_same_event_id_with_conflicting_payload_is_reported() -> None:
    group = TradeGroup(
        ("T205", 3),
        source=[
            Record("T205", 3, 2, "E205V2", "FILLED", "8.0000"),
            Record("T205", 3, 2, "E205V2", "FILLED", "8.5000"),
        ],
        target=[Record("T205", 3, 2, "E205V2", "FILLED", "8.0000")],
    )
    report = group.run_checks(presence_chain())
    changed = report.issues_of("changed")
    assert len(changed) == 1
    assert changed[0].details["reason"] == "payload_conflict"
    assert changed[0].details["event_id"] == "E205V2"
    assert changed[0].details["side"] == "source"
    assert changed[0].details["version"] == 2
    assert {entry["pnl"] for entry in changed[0].details["records"]} == {
        "8.0000", "8.5000"
    }
    assert report.issues_of("duplicates") == []


@pytest.mark.parametrize("side", [Side.SOURCE, Side.TARGET])
def test_changed_conflict_detected_on_either_side(side: str) -> None:
    """The other side's presence must not suppress a local payload conflict."""
    first = Record("T205", 3, 2, "E205V2", "FILLED", "8.0000")
    conflicting = Record("T205", 3, 2, "E205V2", "FILLED", "8.5000")
    group = TradeGroup(
        ("T205", 3),
        source=[first, conflicting] if side == Side.SOURCE else [],
        target=[first, conflicting] if side == Side.TARGET else [],
    )

    report = group.run_checks(presence_chain())
    changed = report.issues_of("changed")
    assert len(changed) == 1
    assert changed[0].details["reason"] == "payload_conflict"
    assert changed[0].details["side"] == side
    assert changed[0].details["event_id"] == "E205V2"


def test_identical_replay_produces_duplicate_but_not_changed() -> None:
    row = Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")
    group = TradeGroup(
        ("T201", 1),
        source=[row, Record("T201", 1, 2, "E201V2", "FILLED", "7.0000")],
        target=[row],
    )

    report = group.run_checks(presence_chain())
    assert len(report.issues_of("duplicates")) == 1
    assert report.issues_of("changed") == []


def test_changed_state_mismatch_provides_reason_and_field() -> None:
    group = TradeGroup(
        ("T201", 1),
        source=[Record("T201", 1, 2, "S2", "FILLED", "7.0001")],
        target=[Record("T201", 1, 2, "T2", "NEW", "7.0000")],
    )
    report = group.run_checks(presence_chain())
    assert {
        (issue.details["reason"], issue.details["field"])
        for issue in report.issues_of("changed")
    } == {("state_mismatch", "pnl"), ("state_mismatch", "status")}


def test_equivalent_decimal_pnl_is_not_changed() -> None:
    group = TradeGroup(
        ("T201", 1),
        source=[Record("T201", 1, 2, "S2", "FILLED", "7.00")],
        target=[Record("T201", 1, 2, "T2", "FILLED", "7.0000")],
    )
    assert group.run_checks(presence_chain()).issues_of("changed") == []


def test_historical_same_version_payload_conflict_is_visible() -> None:
    """Conflicting historical data must not be silently lost to latest()."""
    group = TradeGroup(
        ("T205", 3),
        source=[
            Record("T205", 3, 1, "E1", "NEW", "4.0000"),
            Record("T205", 3, 1, "E1", "NEW", "4.5000"),
            Record("T205", 3, 2, "E2", "FILLED", "8.0000"),
        ],
        target=[Record("T205", 3, 2, "E2", "FILLED", "8.0000")],
    )
    result = group.run_checks(presence_chain())
    conflicts = [issue for issue in result.issues_of("changed") if issue.details.get("reason") == "payload_conflict"]
    assert len(conflicts) == 1
    assert conflicts[0].details["version"] == 1



@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="Raw-row validation before grouping is not implemented",
)
@pytest.mark.parametrize(
    ("side", "raw"),
    [
        (
            "source",
            {
                "trade_id": None,
                "account_id": 4,
                "version": 1,
                "event_id": "src-16",
                "status": "NEW",
                "pnl": "0",
            },
        ),
        (
            "target",
            {
                "trade_id": None,
                "account_id": 4,
                "version": 1,
                "event_id": "tgt-18",
                "status": "SUCCESS",
                "pnl": "0",
            },
        ),
        (
            "target",
            {
                "trade_id": "T114",
                "account_id": None,
                "version": 1,
                "event_id": "tgt-28",
                "status": "SUCCESS",
                "pnl": "0",
            },
        ),
    ],
)
def test_lab04_invalid_business_key_is_not_silently_dropped(
    side: str, raw: dict
) -> None:
    # Adapted from lab04 rows with missing identifiers; details must preserve
    # a reason and side even when no TradeGroup can be constructed.
    source, target = ([raw], []) if side == "source" else ([], [raw])
    report = compare_events(source, target)
    assert any(
        issue["details"].get("side") == side and issue["details"].get("reason")
        for issue in report["malformed"]
    )
