"""Synthetic source manifest in PostgreSQL followed by Kafka event publishing.

Run IDs isolate every attempt. Source rows are committed *before* producing, so a
lost Kafka delivery remains detectable. This is not a distributed transaction.
"""
from __future__ import annotations

import argparse
import json
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from confluent_kafka import Producer

from common import KAFKA_BOOTSTRAP, PG_DSN

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "trades.json"
SCENARIOS = ("clean", "replay", "missing", "conflict", "out_of_order", "corrupt")


def build_events(run_id: str, scenario: str, *, now: datetime | None = None) -> tuple[list[dict], list[dict]]:
    """Return immutable source manifest and synthetic Kafka deliveries."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    now = now or datetime.now(timezone.utc)
    events = []
    for item in json.loads(FIXTURE.read_text(encoding="utf-8")):
        event = {k: v for k, v in item.items() if k != "event_time_offset_seconds"}
        event["run_id"] = run_id
        event["event_time"] = (
            now + timedelta(seconds=item["event_time_offset_seconds"])
        ).isoformat(timespec="milliseconds")
        Decimal(event["pnl"])
        events.append(event)
    if scenario == "conflict":
        conflict = deepcopy(next(e for e in events if e["event_id"] == "E02"))
        conflict.update(event_id="E07", pnl="12.00")
        events.append(conflict)

    deliveries = deepcopy(events)
    if scenario == "replay":
        deliveries.append(deepcopy(next(e for e in events if e["event_id"] == "E02")))
    elif scenario == "missing":
        deliveries = [e for e in deliveries if e["event_id"] != "E03"]
    elif scenario == "out_of_order":
        older = next(e for e in deliveries if e["event_id"] == "E01")
        deliveries = [e for e in deliveries if e["event_id"] != "E01"] + [older]
    elif scenario == "corrupt":
        next(e for e in deliveries if e["event_id"] == "E02")["pnl"] = "999.00"
    return events, deliveries


def register_source(run_id: str, scenario: str, events: list[dict]) -> None:
    if not events or len({e["event_id"] for e in events}) != len(events):
        raise ValueError("Invalid source manifest")
    with psycopg.connect(PG_DSN) as conn:
        conn.execute(
            "INSERT INTO streaming_lab.batches(run_id,scenario,planned_count) VALUES(%s,%s,%s)",
            (run_id, scenario, len(events)),
        )
        for e in events:
            conn.execute(
                """INSERT INTO streaming_lab.source_events
                (run_id,event_id,trade_id,account_id,version,status,pnl,event_time)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (e["run_id"], e["event_id"], e["trade_id"], e["account_id"],
                 e["version"], e["status"], Decimal(e["pnl"]), e["event_time"]),
            )


def publish(deliveries: list[dict]) -> None:
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP,
                         "enable.idempotence": True, "acks": "all"})
    failures = []

    def report(error, message):
        if error is not None:
            failures.append(str(error))

    for event in deliveries:
        key = f'{event["run_id"]}:{event["account_id"]}:{event["trade_id"]}'
        producer.produce("trade-events", key=key.encode(),
                         value=json.dumps(event, sort_keys=True).encode(),
                         on_delivery=report)
        producer.poll(0)
    remaining = producer.flush(30)
    if failures or remaining:
        raise RuntimeError(f"Kafka publish failed: failures={failures}, remaining={remaining}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="clean")
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()
    run_id = args.run_id or uuid.uuid4().hex
    if len(run_id) > 80 or not all(c.isalnum() or c in "-_" for c in run_id):
        parser.error("--run-id must be <=80 alphanumeric, dash or underscore characters")
    events, deliveries = build_events(run_id, args.scenario)
    register_source(run_id, args.scenario, events)
    publish(deliveries)
    # Manifest publication is a two-system boundary, not an atomic
    # transaction. A PENDING run must never be treated as a DQ PASS/FAIL.
    with psycopg.connect(PG_DSN) as conn:
        conn.execute(
            "UPDATE streaming_lab.batches "
            "SET publication_status='PUBLISHED', published_at=now() "
            "WHERE run_id=%s AND publication_status='PENDING'",
            (run_id,),
        )
    print(f"RUN_ID={run_id}", flush=True)
    print(json.dumps({"run_id":run_id,"scenario":args.scenario,
                      "source_manifest_events":len(events),"kafka_deliveries":len(deliveries)}))


if __name__ == "__main__":
    main()
