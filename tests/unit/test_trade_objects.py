"""Only structural scaffold tests: not a solution for reconciliation."""

import pytest
from data_qa.checkers.base import AbstractChecker

from data_qa.data.trade_group import Record, TradeGroup
from data_qa.data.trade_result import TradeResult


def test_record_business_key_is_typed_tuple() -> None:
    assert Record(trade_id="T1", account_id=100).business_key() == ("T1", 100)


def test_group_holds_both_sides_without_modifying_input_lists() -> None:
    source = [Record(trade_id="T1", account_id=100, event_id="E1")]
    group = TradeGroup(business_key=("T1", 100), source=source)
    group.add_target(Record(trade_id="T1", account_id=100, event_id="E2"))

    assert len(group.source) == 1
    assert len(group.target) == 1
    assert len(source) == 1


@pytest.mark.parametrize("side", ["source", "target"])
def test_group_rejects_events_from_other_trade(side: str) -> None:
    """An event for another account must never enter either side of this group."""
    group = TradeGroup(business_key=("T1", 100))
    wrong_record = Record(trade_id="T1", account_id=200, event_id="E3")

    with pytest.raises(ValueError, match="belongs to") as error:
        getattr(group, f"add_{side}")(wrong_record)

    assert repr(wrong_record.business_key()) in str(error.value)
    assert repr(group.business_key) in str(error.value)
    assert group.source == []
    assert group.target == []


def test_result_accumulates_multiple_findings_for_one_key() -> None:
    result = TradeResult(business_key=("T1", 100))
    result.add_issue("changed", source_version=2, target_version=1)
    result.add_issue("duplicates", side="source", event_id="E2")

    assert result.has_issues
    assert len(result.issues) == 2
    assert result.issues_of("changed")[0].details["source_version"] == 2


def test_group_runs_each_checker_and_accumulates_issues() -> None:
    class MissingChecker(AbstractChecker):
        def handle(self, group: TradeGroup, result: TradeResult) -> None:
            if not group.target:
                result.add_issue("missing", source_count=len(group.source))
            return super().handle(group, result)
    class DuplicateChecker(AbstractChecker):
        def handle(self, group: TradeGroup, result: TradeResult) -> None:
            if len(group.source) > 1:
                result.add_issue("duplicates", side="source")
            return super().handle(group, result)

    group = TradeGroup(
        business_key=("T1", 100),
        source=[
            Record(trade_id="T1", account_id=100, event_id="E1"),
            Record(trade_id="T1", account_id=100, event_id="E1"),
        ],
    )
    data_checkers = MissingChecker()
    data_checkers.set_next(DuplicateChecker())
    result = group.run_checks(data_checkers)
    assert [issue.category for issue in result.issues] == ["missing", "duplicates"]
