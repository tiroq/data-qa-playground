"""Session 05: source-to-target trading-event reconciliation.

Exercise starter only: implement compare_events yourself.
No database, network or framework dependencies.
"""

from typing import Any, TypedDict

Event = dict[str, Any]
class Issue(TypedDict):
    """One issue for a single business key, or unkeyed malformed input.

    No overall boolean status is returned for the batch.
    trade_id/account_id can be None only when the invalid input cannot
    supply a valid key; details must explain the mismatch or error.
    """

    trade_id: str | None
    account_id: int | None
    details: dict[str, Any]


class ComparisonReport(TypedDict):
    missing: list[Issue]
    extra: list[Issue]
    changed: list[Issue]
    duplicates: list[Issue]
    malformed: list[Issue]


def compare_events(source: list[Event], target: list[Event]) -> ComparisonReport:
    """Compare trading events without mutating source or target.

    Business key: (trade_id, account_id).
    Current state: highest version per business key.
    Compare current version, status and pnl (using Decimal).

    Inputs are entire event datasets (not one row or one trade).
    Output is ONE report with five LISTS of individual, business-keyed
    issues; it is never a single batch-level missing/changed flag.
    Correctly matched trades need not appear in any list.
    Every issue contains trade_id, account_id, and details. Only malformed
    input may have a missing/null business key, with a reason in details.

    Classify missing, extra, changed, duplicate and malformed events.
    Do not silently overwrite conflicting events or versions.
    Return deterministic diagnostics regardless of input ordering.

    TODO:
      1. Validate input rows and retain malformed diagnostics.
      2. Detect duplicate delivery versus conflicting event payloads.
      3. Build latest-version state for each business key.
      4. Compare source/target; retain identifiers and differing values.
      5. Sort report entries deterministically.

    Raise NotImplementedError until you have a real implementation.
    """
    raise NotImplementedError("Session 05: implement compare_events")
