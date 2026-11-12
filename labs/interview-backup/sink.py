"""At-least-once Kafka -> ClickHouse raw delivery adapter.

Commit offset only AFTER HTTP write acknowledgement. The ACK and Kafka commit
are not atomic: crash between them can duplicate a physical ClickHouse row.
That is intentional and checked separately at business/event identity grain.
"""
from __future__ import annotations

import json
import logging
import os
import time

from confluent_kafka import Consumer

from common import KAFKA_BOOTSTRAP, clickhouse_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("streaming_sink")
REQUIRED = ("run_id","event_id","trade_id","account_id","version",
            "status","pnl","event_time","source_tag")
INSERT = "INSERT INTO streaming_lab.raw_events FORMAT JSONEachRow"


def row_for_message(payload: dict, *, topic: str, partition: int, offset: int) -> dict:
    missing = [key for key in REQUIRED if key not in payload]
    if missing:
        raise ValueError(f"Missing processed message fields: {missing}")
    if payload["source_tag"] != "flink_sql":
        raise ValueError("Source tag mismatch: expected Flink SQL transform")
    return {**{key: payload[key] for key in REQUIRED},
            "kafka_topic":topic, "kafka_partition":partition, "kafka_offset":offset}


def main() -> None:
    consumer = Consumer({
        "bootstrap.servers":KAFKA_BOOTSTRAP,
        "group.id":os.getenv("SINK_GROUP","trading-lab-clickhouse-sink-v1"),
        "auto.offset.reset":"earliest",
        "enable.auto.commit":False,
        "enable.auto.offset.store":False,
    })
    consumer.subscribe(["processed-trades"])
    log.info("Kafka-to-ClickHouse sink subscribed; offsets commit after acknowledged INSERT")
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                log.warning("Kafka poll error: %s", message.error())
                continue
            try:
                payload = json.loads(message.value())
                row = row_for_message(payload, topic=message.topic(),
                                      partition=message.partition(), offset=message.offset())
                clickhouse_query(INSERT, data=(json.dumps(row)+"\n").encode())
                consumer.store_offsets(message=message)
                consumer.commit(asynchronous=False)
            except Exception:
                log.exception("Sink write/commit failed, stopping to force replay; physical duplicates may occur")
                raise
    finally:
        consumer.close()


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception:
            time.sleep(3)
