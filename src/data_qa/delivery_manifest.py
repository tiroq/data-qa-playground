"""Session 07 physical delivery manifest reconciliation.

This deliberately narrow checker compares event IDs and physical multiplicity.
It does NOT reconcile payload, business-key versions, or latest trade state.
Those remain independent DQ checks.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DeliveryReport:
    """Exact missing/unexpected IDs and repeated physical target deliveries."""

    missing: frozenset[str]
    unexpected: frozenset[str]
    duplicates: dict[str, int]

    @property
    def passed(self) -> bool:
        return not (self.missing or self.unexpected or self.duplicates)


def reconcile_delivery(
    expected: Sequence[str],
    actual: Sequence[str],
    *,
    planned_count: int,
) -> DeliveryReport:
    """Compare a predeclared, unique source event manifest with target rows.

    `planned_count` must come from the independent test scenario contract;
    it is *not* inferred from target or source query row counts.

    Preconditions:
    - Each expected event ID is unique (one logical source event per ID).
    - The processing-completion barrier was verified separately.
    - An intentional empty scenario explicitly declares planned_count=0.

    Expected time complexity: O(len(expected) + len(actual)).
    """
    if type(planned_count) is not int or planned_count < 0:
        raise ValueError("planned_count must be a nonnegative integer")
    if len(expected) != planned_count:
        raise ValueError(
            f"Expected manifest has {len(expected)} events, "
            f"but the test scenario planned {planned_count}"
        )

    expected_ids = set(expected)
    if len(expected_ids) != len(expected):
        raise ValueError("Expected manifest contains duplicate event IDs")

    counts = Counter(actual)
    actual_ids = set(counts)

    return DeliveryReport(
        missing=frozenset(expected_ids - actual_ids),
        unexpected=frozenset(actual_ids - expected_ids),
        duplicates={event_id: count for event_id, count in counts.items() if count > 1},
    )
