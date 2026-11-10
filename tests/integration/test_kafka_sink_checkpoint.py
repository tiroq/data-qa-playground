"""Real Kafka offsets + ClickHouse sink test in two disposable containers.

A committed consumer offset is NOT a sink-side durability acknowledgment.
Two Kafka partitions deliberately demonstrate that there is no global offset.
"""
from __future__ import annotations

import json
import time
from decimal import Decimal
from uuid import uuid4

import pytest

from data_qa.delivery_manifest import reconcile_delivery

pytestmark = pytest.mark.kafka


@pytest.fixture(scope="session")
def kafka_bootstrap():
    from testcontainers.kafka import KafkaContainer

    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as broker:
        yield broker.get_bootstrap_server()


def test_zero_lag_before_sink_write_does_not_prove_delivery(
    kafka_bootstrap, ch_client, ch_trade_tables
):
    from confluent_kafka import Consumer, Producer, TopicPartition
    from confluent_kafka.admin import AdminClient, NewTopic

    topic = f"session07-{uuid4().hex}"
    admin = AdminClient({"bootstrap.servers": kafka_bootstrap})
    admin.create_topics(
        [NewTopic(topic, num_partitions=2, replication_factor=1)]
    )[topic].result(timeout=20)

    expected = [
        {"event_id": "E-1", "trade_id": f"T-{uuid4().hex}", "account_id": "A1",
         "version": 1, "pnl": "15.50", "status": "FILLED"},
        {"event_id": "E-2", "trade_id": f"T-{uuid4().hex}", "account_id": "A1",
         "version": 2, "pnl": "20.00", "status": "FILLED"},
    ]

    producer = Producer({"bootstrap.servers": kafka_bootstrap})
    for partition, event in enumerate(expected):
        producer.produce(
            topic, partition=partition, key=event["event_id"].encode(),
            value=json.dumps(event).encode(),
        )
    assert producer.flush(timeout=20) == 0

    consumer = Consumer({
        "bootstrap.servers": kafka_bootstrap,
        "group.id": f"session07-{uuid4().hex}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "enable.auto.offset.store": False,
    })
    try:
        consumer.assign([TopicPartition(topic, 0, 0), TopicPartition(topic, 1, 0)])
        messages = []
        deadline = time.monotonic() + 20
        while len(messages) < 2 and time.monotonic() < deadline:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise AssertionError(f"Kafka poll error: {message.error()}")
            messages.append(message)
        assert len(messages) == 2, f"Only received {len(messages)} Kafka messages"
        assert {message.partition() for message in messages} == {0, 1}

        # Bad practice on purpose: committing offsets before ClickHouse writes.
        offsets = [
            TopicPartition(topic, message.partition(), message.offset() + 1)
            for message in messages
        ]
        result = consumer.commit(offsets=offsets, asynchronous=False)
        assert len(result) == 2
        assert all(entry.error is None for entry in result)
        acknowledged = consumer.committed(
            [TopicPartition(topic, 0), TopicPartition(topic, 1)], timeout=10,
        )
        for entry in acknowledged:
            _, high = consumer.get_watermark_offsets(
                TopicPartition(topic, entry.partition), timeout=10
            )
            assert high == entry.offset, f"Nonzero lag for partition {entry.partition}"

        # Real Kafka group lag is zero, but ClickHouse raw is still EMPTY.
        db = ch_trade_tables
        assert ch_client.execute(f"SELECT count() FROM {db}.trade_events_raw") == [(0,)]
        missing = reconcile_delivery(
            [event["event_id"] for event in expected], [], planned_count=2,
        )
        assert missing.missing == {"E-1", "E-2"} and not missing.passed

        # A last-delivered event is not sufficient either: E-2 arrived, E-1 did not.
        last = expected[1]
        ch_client.execute(
            f"INSERT INTO {db}.trade_events_raw "
            "(event_id, trade_id, account_id, version, pnl, status) VALUES",
            [(last["event_id"], last["trade_id"], last["account_id"],
              last["version"], Decimal(last["pnl"]), last["status"])],
        )
        observed = ch_client.execute(
            f"SELECT event_id FROM {db}.trade_events_raw"
        )
        report = reconcile_delivery(
            [event["event_id"] for event in expected],
            [r[0] for r in observed],
            planned_count=2,
        )
        assert report.missing == {"E-1"} and not report.passed

        # Complete the sink writes then compare actual event IDs.
        first = expected[0]
        ch_client.execute(
            f"INSERT INTO {db}.trade_events_raw "
            "(event_id, trade_id, account_id, version, pnl, status) VALUES",
            [(first["event_id"], first["trade_id"], first["account_id"],
              first["version"], Decimal(first["pnl"]), first["status"])],
        )
        observed = ch_client.execute(f"SELECT event_id FROM {db}.trade_events_raw")
        report = reconcile_delivery(
            [event["event_id"] for event in expected],
            [r[0] for r in observed],
            planned_count=2,
        )
        assert report.passed
    finally:
        consumer.close()
