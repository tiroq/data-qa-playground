-- PREPARATION ONLY. Destructively resets lab09, never lab03.
-- Reproduce raw Session 03 version deliveries in a separate exercise namespace.
DROP DATABASE IF EXISTS lab09;
CREATE DATABASE lab09;

CREATE TABLE lab09.raw_events
(
    ingest_id   UInt64,
    trade_id    UInt64,
    account_id  String,
    version     UInt32,
    event_time  DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    pnl         Nullable(Decimal(18, 4)),
    status      Nullable(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (account_id, trade_id, ingest_id);

INSERT INTO lab09.raw_events SELECT * FROM lab03.trade_versions;
