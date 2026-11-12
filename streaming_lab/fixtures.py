"""Generate deterministic synthetic trading events and source manifest SQL.

Only the scenario and run_id vary; the event contract remains stable. The
generated manifest is independently inserted into PostgreSQL BEFORE Kafka
publishing, and sealed only after successful CLI publication.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

RUN_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,48}$")
SCENARIOS = ("healthy", "duplicate", "missing", "corrupt", "out_of_order",
             "conflict", "extra")


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must contain 1..48 ASCII letters, digits, _ or -")
    return run_id


def make_fixture(run_id: str, scenario: str, *, base_time_ms: int) -> tuple[list[dict], list[dict]]:
    """Return (authoritative expected events, physical Kafka deliveries)."""
    validate_run_id(run_id)
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown training scenario: {scenario}")

    rows = [
        ("E001", "T100", "A1", 1, "0.00", "NEW"),
        ("E002", "T100", "A1", 2, "10.00", "FILLED"),
        ("E003", "T101", "A1", 1, "-2.50", "FILLED"),
        ("E004", "T200", "A2", 1, "0.00", "NEW"),
        ("E005", "T200", "A2", 2, "7.00", "FILLED"),
        ("E006", "T201", "A2", 1, "4.00", "FILLED"),
    ]
    expected = [
        dict(run_id=run_id, event_id=event_id, trade_id=trade,
             account_id=account, version=version, pnl=pnl, status=status,
             event_time_ms=base_time_ms + index * 100)
        for index, (event_id, trade, account, version, pnl, status) in enumerate(rows)
    ]
    if scenario == "conflict":
        expected.append({
            **expected[1], "event_id": "E007", "pnl": "10.25",
            "event_time_ms": base_time_ms + 600
        })
    published = [dict(event) for event in expected]
    if scenario == "duplicate":
        published.append(dict(expected[1]))  # physical replay, same immutable ID/payload
    elif scenario == "missing":
        published = [item for item in published if item["event_id"] != "E004"]
    elif scenario == "corrupt":
        published[2]["pnl"] = "-999.00"  # source manifest unchanged, corrupt target payload
    elif scenario == "out_of_order":
        published[0], published[1] = published[1], published[0]
        published[3], published[4] = published[4], published[3]
    elif scenario == "extra":
        published.append({
            **expected[-1], "event_id": "E999", "trade_id": "T999", "account_id": "A9"
        })
    return expected, published


def quote_sql(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def render_sql(run_id: str, scenario: str, expected: list[dict]) -> tuple[str, str]:
    validate_run_id(run_id)
    lines = [
        "BEGIN;",
        "INSERT INTO labstream.runs (run_id, scenario, planned_events, sealed)",
        f"VALUES ({quote_sql(run_id)}, {quote_sql(scenario)}, {len(expected)}, FALSE);",
    ]
    for row in expected:
        lines.extend([
            "INSERT INTO labstream.expected_events",
            "(run_id,event_id,trade_id,account_id,version,pnl,status,event_time_ms)",
            "VALUES ("
            + ",".join([
                quote_sql(row["run_id"]), quote_sql(row["event_id"]),
                quote_sql(row["trade_id"]), quote_sql(row["account_id"]),
                str(row["version"]), quote_sql(row["pnl"]), quote_sql(row["status"]),
                str(row["event_time_ms"]),
            ])
            + ");",
        ])
    lines.append("COMMIT;")
    seal = (
        "UPDATE labstream.runs SET sealed = TRUE WHERE run_id = "
        + quote_sql(run_id) + " AND sealed = FALSE;\n"
    )
    return "\n".join(lines) + "\n", seal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="healthy")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--time-ms", type=int, default=None,
                        help="Optional deterministic timestamp for repeatable tests")
    args = parser.parse_args()
    timestamp = args.time_ms if args.time_ms is not None else int(time.time() * 1000)
    expected, published = make_fixture(args.run_id, args.scenario, base_time_ms=timestamp)
    dest = args.output_dir
    dest.mkdir(parents=True, exist_ok=True)
    manifest_sql, seal_sql = render_sql(args.run_id, args.scenario, expected)
    (dest / "manifest.sql").write_text(manifest_sql, encoding="utf-8")
    (dest / "seal.sql").write_text(seal_sql, encoding="utf-8")
    (dest / "expected.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in expected),
        encoding="utf-8",
    )
    (dest / "events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in published),
        encoding="utf-8",
    )
    print(json.dumps({"run_id": args.run_id, "scenario": args.scenario,
                      "expected_events": len(expected),
                      "published_deliveries": len(published),
                      "out": str(dest)}, sort_keys=True))


if __name__ == "__main__":
    main()
