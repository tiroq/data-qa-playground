"""Commit failures must abort the ClickHouse sink so Kafka can replay."""
import importlib
import json
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class SinkCommitTest(unittest.TestCase):
    def test_partition_commit_error_aborts_sink(self):
        event = dict(run_id="r1", event_id="E1", trade_id="T1",
                     account_id="A1", version=1, status="FILLED", pnl="1",
                     event_time="2026-11-12T12:00:00Z", source_tag="flink_sql")
        message = Mock()
        message.error.return_value = None
        message.value.return_value = json.dumps(event).encode()
        message.topic.return_value = "processed-trades"
        message.partition.return_value = 0
        message.offset.return_value = 12
        consumer = Mock()
        consumer.poll.return_value = message
        consumer.commit.return_value = [SimpleNamespace(
            topic="processed-trades", partition=0, offset=13, error="not committed")]
        fake_kafka = types.ModuleType("confluent_kafka")
        fake_kafka.Consumer = Mock(return_value=consumer)
        with patch.dict(sys.modules, {"confluent_kafka": fake_kafka}):
            sys.modules.pop("sink", None)
            sink = importlib.import_module("sink")
        with patch.object(sink, "clickhouse_query"):
            with self.assertRaisesRegex(RuntimeError, "Kafka offset commit failed"):
                sink.main()
        consumer.commit.assert_called_once_with(asynchronous=False)
        consumer.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
