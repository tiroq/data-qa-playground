"""Data quality responsibilities are separated from delivery multiplicity."""
from decimal import Decimal

from data_qa.delivery_quality import conflicting_versions, mismatched_event_payloads


def trade(event_id="E1", pnl="15.50", version=1, status="FILLED"):
    return dict(event_id=event_id, trade_id="T1", account_id="A1",
                version=version, pnl=pnl, status=status)


def test_same_version_conflicting_pnl_is_not_just_duplicate():
    rows = [trade("E1"), trade("E2", pnl="17.00")]
    assert conflicting_versions(rows) == {
        ("T1", "A1", 1): {(Decimal("15.50"), "FILLED"), (Decimal("17.00"), "FILLED")}
    }


def test_identical_repeated_event_is_delivery_duplicate_not_payload_conflict():
    first = trade()
    assert conflicting_versions([first, first]) == {}
    assert mismatched_event_payloads([first], [first, first]) == {}


def test_payload_checker_sees_same_event_id_with_wrong_pnl():
    expected = [trade()]
    actual = [trade(), trade(pnl="18.00")]
    mismatches = mismatched_event_payloads(expected, actual)
    assert set(mismatches) == {"E1"}
    assert len(mismatches["E1"][1]) == 2


def test_decimal_scale_is_not_a_payload_mismatch():
    assert mismatched_event_payloads([trade(pnl="7.0")], [trade(pnl="7.00")]) == {}


def test_payload_checker_does_not_reclassify_missing_as_mismatch():
    assert mismatched_event_payloads([trade()], []) == {}
