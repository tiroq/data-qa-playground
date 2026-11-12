-- A real Flink SQL streaming INSERT: Kafka source -> Kafka processed topic.
-- Business PnL is a snapshot value, not a delta; no account aggregation is done here.
-- No claim of end-to-end exactly-once through the external ClickHouse sink.
SET 'execution.runtime-mode' = 'streaming';
SET 'parallelism.default' = '1';
SET 'execution.checkpointing.interval' = '5 s';
SET 'pipeline.name' = 'trade-pipeline-lab';
SET 'table.dml-sync' = 'false';

CREATE TABLE trade_events (
  run_id STRING,
  event_id STRING,
  trade_id STRING,
  account_id STRING,
  version INT,
  status STRING,
  pnl STRING,
  event_time STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'trade-events',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'trading-lab-flink',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false'
);

CREATE TABLE processed_trades (
  business_key STRING,
  run_id STRING,
  event_id STRING,
  trade_id STRING,
  account_id STRING,
  version INT,
  status STRING,
  pnl STRING,
  event_time STRING,
  source_tag STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'processed-trades',
  'properties.bootstrap.servers' = 'kafka:9092',
  'key.format' = 'json',
  'key.fields' = 'business_key',
  'value.format' = 'json',
  'value.fields-include' = 'EXCEPT_KEY',
  'sink.delivery-guarantee' = 'at-least-once'
);

INSERT INTO processed_trades
SELECT CONCAT(run_id, ':', account_id, ':', trade_id) AS business_key,
       run_id, event_id, trade_id, account_id, version, status, pnl,
       event_time, 'flink_sql' AS source_tag
FROM trade_events;
