"""Only structural scaffold tests: not a solution for reconciliation."""

import pytest

from data_qa.data import Record, TradeGroup, TradeResult


def test_record_business_key_is_typed_tuple() -> None:
    assert Record(trade_id="T1", account_id=100).business_key() == ("T1", 100)


def test_group_holds_both_sides_without_modifying_input_lists() -> None:
    source = [Record(trade_id="T1", account_id=100, event_id="E1")]
    group = TradeGroup(business_key=("T1", 100), source=source)
    group.add_target(Record(trade_id="T1", account_id=100, event_id="E2"))

    assert len(group.source) == 1
    assert len(group.target) == 1
    assert len(source) == 1


def test_group_rejects_events_from_other_trade() -> None:
    group = TradeGroup(business_key=("T1", 100))
    with pytest.raises(ValueError, match="belongs to"):
        group.add_source(Record(trade_id="T1", account_id=200, event_id="E3"))


def test_result_accumulates_multiple_findings_for_one_key() -> None:
    result = TradeResult(business_key=("T1", 100))
    result.add_issue("changed", source_version=2, target_version=1)
    result.add_issue("duplicates", side="source", event_id="E2")

    assert result.has_issues
    assert len(result.issues) == 2
    assert result.issues_of("changed")[0].details["source_version"] == 2


def test_group_runs_each_checker_and_accumulates_issues() -> None:
    class MissingChecker:
        def check(self, group: TradeGroup, result: TradeResult) -> None:
            if not group.target:
                result.add_issue("missing", source_count=len(group.source))

    class DuplicateChecker:
        def check(self, group: TradeGroup, result: TradeResult) -> None:
            if len(group.source) > 1:
                result.add_issue("duplicates", side="source")

    group = TradeGroup(
        business_key=("T1", 100),
        source=[
            Record(trade_id="T1", account_id=100, event_id="E1"),
            Record(trade_id="T1", account_id=100, event_id="E1"),
        ],
    )
    result = group.run_checks([MissingChecker(), DuplicateChecker()])
    assert [issue.category for issue in result.issues] == ["missing", "duplicates"]
