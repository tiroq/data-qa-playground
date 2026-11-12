"""Verify observed ClickHouse raw events against independent PostgreSQL manifest.

Example:
  python /app/check.py --run-id <UUID> --expect PASS --wait-seconds 90
  python /app/check.py --run-id <UUID> --expect FAIL --require-rule missing_event

A passing snapshot is NOT a durable end-of-batch completion certificate:
the lab has no atomic Kafka-offset/ClickHouse-sink checkpoint protocol.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import psycopg

from common import PG_DSN, clickhouse_query, parse_json_rows
from dq import evaluate


def source_manifest(run_id: str) -> tuple[int,list[dict],str,str]:
    with psycopg.connect(PG_DSN) as conn:
        batch = conn.execute(
            "SELECT planned_count,scenario,publication_status FROM streaming_lab.batches WHERE run_id=%s",
            (run_id,),
        ).fetchone()
        if batch is None:
            raise ValueError(f"Unknown run ID: {run_id}")
        rows = conn.execute(
            """SELECT event_id,trade_id,account_id,version,status,pnl,event_time
               FROM streaming_lab.source_events WHERE run_id=%s""", (run_id,),
        ).fetchall()
    return batch[0], [
        dict(event_id=r[0],trade_id=r[1],account_id=r[2],
             version=r[3],status=r[4],pnl=str(r[5]),event_time=r[6])
        for r in rows
    ], batch[1], batch[2]


def clickhouse_observations(run_id: str) -> list[dict]:
    if len(run_id)>80 or not run_id or not all(c.isalnum() or c in "-_" for c in run_id):
        raise ValueError("Invalid run ID")
    q = ("""SELECT run_id,event_id,trade_id,account_id,version,status,pnl,
               event_time,source_tag,kafka_topic,kafka_partition,kafka_offset
               FROM streaming_lab.raw_events
               WHERE run_id = {rid:String} FORMAT JSONEachRow""")
    return parse_json_rows(clickhouse_query(q, params={"param_rid":run_id}))


class PublicationIncomplete(Exception):
    """Source manifest exists but producer has not committed publication status."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--wait-seconds", type=float, default=90)
    parser.add_argument("--settle-seconds", type=float, default=2)
    parser.add_argument("--expect", choices=["PASS","FAIL","INDETERMINATE"], default="PASS")
    parser.add_argument("--require-rule", default=None,
                        help="Required rule code when expecting a known negative scenario")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.wait_seconds < 0 or args.settle_seconds < 0:
        parser.error("Wait and settle durations must be nonnegative")
    try:
        planned, source, scenario, publication_status = source_manifest(args.run_id)
        if publication_status != "PUBLISHED":
            raise PublicationIncomplete(
                f"Source batch not sealed: publication_status={publication_status}"
            )
        deadline = time.monotonic() + args.wait_seconds
        fully_visible_since = None
        while True:
            actual = clickhouse_observations(args.run_id)
            report = evaluate(args.run_id, planned, source, actual)
            seen_all = report["observed_distinct"] >= report["expected_distinct"] and not any(
                issue["rule"] == "missing_event" for issue in report["issues"]
            )
            now = time.monotonic()
            if report["status"] == "ERROR":
                break
            if seen_all:
                if fully_visible_since is None:
                    fully_visible_since = now
                if now - fully_visible_since >= args.settle_seconds:
                    break
            else:
                fully_visible_since = None
            if now >= deadline:
                break
            time.sleep(min(0.5, max(0.0, deadline-now)))
        report["scenario"] = scenario
        report["evaluation_note"] = (
            "Comparison of current persisted observations; NOT a proof of sink completion "
            "or of future absence of late conflicting events"
        )
    except PublicationIncomplete as exc:
        report = {"run_id":args.run_id,"status":"INDETERMINATE","issues":[
            {"rule":"publication_incomplete","detail":str(exc)}]}
    except Exception as exc:
        report = {"run_id":args.run_id,"status":"ERROR","issues":[
            {"rule":"infrastructure_or_manifest_error","detail":f"{type(exc).__name__}: {exc}"}]}
    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    print(payload)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload+"\n", encoding="utf-8")
    rules = {i["rule"] for i in report.get("issues",[])}
    valid = report["status"] == args.expect and (
        args.require_rule is None or args.require_rule in rules
    )
    # Infrastructure or invalid source manifest is NEVER a successful expected FAIL.
    if report["status"] == "ERROR":
        valid = False
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
