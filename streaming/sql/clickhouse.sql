-- Non-destructive lab-only schema. The Kafka table is a consumer; attaching
-- its MV can start consumption immediately. Create the topic before executing.
CREATE DATABASE IF NOT EXISTS labstream;

CREATE TABLE IF NOT EXISTS labstream.raw_events (
  run_id String,
  event_id String,
  trade_id String,
  account_id String,
  version Int32,
  pnl String,
  status String,
  event_time_ms Int64,
  available_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(available_at)
ORDER BY (run_id, account_id, trade_id, version, event_id, available_at);

CREATE TABLE IF NOT EXISTS labstream.kafka_processed (
  run_id String,
  event_id String,
  trade_id String,
  account_id String,
  version Int32,
  pnl String,
  status String,
  event_time_ms Int64
)
ENGINE = Kafka
SETTINGS
  kafka_broker_list = 'kafka:9092',
  kafka_topic_list = 'trade-processed',
  kafka_group_name = 'clickhouse-labstream-sink',
  kafka_format = 'JSONEachRow',
  kafka_num_consumers = 1,
  kafka_skip_broken_messages = 0;

CREATE MATERIALIZED VIEW IF NOT EXISTS labstream.mv_processed_to_raw
TO labstream.raw_events AS
SELECT run_id, event_id, trade_id, account_id, version,
       pnl, status, event_time_ms, now64(3) AS available_at
FROM labstream.kafka_processed;
