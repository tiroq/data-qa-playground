-- Session 03 — Candidate's original DDL attempt (preserved unchanged in substance).
-- Status: proposed in chat; runtime execution not independently verified.
-- Reviewer comments are in ../notes/03-clickhouse-review.md.
CREATE TABLE IF NOT EXISTS lab03.trading_events_latest
(
    ingest_id UInt64,
    account_id String,
    trade_id String,
    version UInt32,
    trade_date Date,
    pnl Nullable(Decimal(18,4))
)
ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(trade_date)
ORDER BY (account_id, trade_id)
;
