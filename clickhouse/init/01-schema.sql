-- Session 03 raw delivery tables, not reference deduplicating solutions.
-- Physical grain: one row per stored delivery/ingest_id.
-- The MergeTree sorting keys are NOT unique constraints.
CREATE DATABASE IF NOT EXISTS lab03;

CREATE TABLE IF NOT EXISTS lab03.trading_events
(
    ingest_id   UInt64,
    account_id  String,
    trade_id    String,
    version     UInt32,
    trade_date  Date,
    event_time  DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    pnl         Nullable(Decimal(18, 4)),
    status      Nullable(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (account_id, trade_id, ingest_id);

-- Mirrors the Session 02 PostgreSQL 12-row dataset. This is a separate
-- physical-delivery log and deliberately preserves duplicates and conflicts.
CREATE TABLE IF NOT EXISTS lab03.trade_versions
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
