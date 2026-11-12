-- Submitted once via scripts/streaming_lab.sh up.
-- The JSON payload stays raw: this job does NOT deduplicate or silently
-- resolve same-version conflicts. That work belongs to the explicit DQ contract.
SET 'pipeline.name' = 'trading-versioned-events-lab';
SET 'execution.checkpointing.interval' = '5s';
SET 'execution.checkpointing.mode' = 'AT_LEAST_ONCE';
SET 'execution.attached' = 'false';

CREATE TABLE trades_in (
    run_id STRING,
    event_id STRING,
    trade_id STRING,
    account_id STRING,
    version INT,
    pnl STRING,
    status STRING,
    event_time_ms BIGINT,
    event_ts AS TO_TIMESTAMP_LTZ(event_time_ms, 3),
    WATERMARK FOR event_ts AS event_ts - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'trades-input',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'flink-trades-lab',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.fail-on-missing-field' = 'true'
);

CREATE TABLE trades_out (
    run_id STRING,
    event_id STRING,
    trade_id STRING,
    account_id STRING,
    version INT,
    pnl STRING,
    status STRING,
    event_time_ms BIGINT
) WITH (
    'connector' = 'kafka',
    'topic' = 'trade-processed',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'sink.delivery-guarantee' = 'at-least-once'
);

INSERT INTO trades_out
SELECT run_id, event_id, trade_id, account_id,
       version, pnl, status, event_time_ms
FROM trades_in;
