-- Append-only physical deliveries: duplicate attempts remain observable.
CREATE DATABASE IF NOT EXISTS streaming_lab;
CREATE TABLE IF NOT EXISTS streaming_lab.raw_events (
  run_id String,
  event_id String,
  trade_id String,
  account_id String,
  version UInt32,
  status String,
  pnl String,
  event_time String,
  source_tag String,
  kafka_topic String,
  kafka_partition Int32,
  kafka_offset Int64,
  available_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree
PARTITION BY toYYYYMM(available_at)
ORDER BY (run_id, account_id, trade_id, event_id, kafka_partition, kafka_offset);
