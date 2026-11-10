"""Orthogonal payload and version checks for physical trade events.

Transport multiplicity is checked independently by delivery_manifest.
No query-time 'winner' from argMax may suppress a conflicting same-version
payload when deciding the quality of a latest-state projection.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Sequence


def payload(row: dict[str, Any]) -> tuple[str, str, int, Decimal, str]:
    return (
        str(row["trade_id"]),
        str(row["account_id"]),
        int(row["version"]),
        Decimal(str(row["pnl"])),
        str(row["status"]),
    )


def conflicting_versions(
    rows: Sequence[dict[str, Any]],
) -> dict[tuple[str, str, int], set[tuple[Decimal, str]]]:
    """Conflicting *payloads* sharing trade/account/version, not duplicates."""
    by_version: dict[
        tuple[str, str, int], set[tuple[Decimal, str]]
    ] = defaultdict(set)
    for row in rows:
        by_version[
            (str(row["trade_id"]), str(row["account_id"]), int(row["version"]))
        ].add((Decimal(str(row["pnl"])), str(row["status"])))
    return {key: values for key, values in by_version.items() if len(values) > 1}


def mismatched_event_payloads(
    expected: Sequence[dict[str, Any]],
    actual: Sequence[dict[str, Any]],
) -> dict[str, tuple[tuple[str, str, int, Decimal, str], set[tuple[str, str, int, Decimal, str]]]]:
    """Compare shared event IDs and ALL physical payloads for each such ID.

    Unexpected and missing IDs belong to the delivery checker, not this one.
    """
    source = {str(row["event_id"]): payload(row) for row in expected}
    if len(source) != len(expected):
        raise ValueError("Expected source event IDs must be unique")
    observed: dict[str, set[tuple[str, str, int, Decimal, str]]] = defaultdict(set)
    for row in actual:
        observed[str(row["event_id"])].add(payload(row))
    return {
        event_id: (expected_payload, observed[event_id])
        for event_id, expected_payload in source.items()
        if event_id in observed and observed[event_id] != {expected_payload}
    }
