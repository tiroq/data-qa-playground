-- Session 04: ClickHouse discussion examples, not PostgreSQL SQL.
-- Requires optional ClickHouse service (docker compose --profile clickhouse).
-- Own isolated ClickHouse database and tables; no changes to lab03.
-- WARNING: this script RESETS the session-owned lab04 schema.
-- These are mentor-authored demonstrations; runtime verification pending.

CREATE DATABASE IF NOT EXISTS lab04;
DROP TABLE IF EXISTS lab04.raw_events;
DROP TABLE IF EXISTS lab04.trades_current;

-- Preserve every physical event. ReplacingMergeTree is intentionally NOT used
-- for this audit log: losing earlier versions defeats historical reconciliation.
CREATE TABLE lab04.raw_events
(
    ingest_id UInt64,
    trade_id UInt64,
    account_id String,
    version UInt32,
    amount Nullable(Int64),
    source_committed_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (trade_id, account_id, ingest_id);

INSERT INTO lab04.raw_events
    (ingest_id, trade_id, account_id, version, amount, source_committed_at)
VALUES
    (1,101,'A1',2,150,'2026-11-08 11:58:00'),
    (2,101,'A1',3,NULL,'2026-11-08 12:03:00'),
    (3,101,'A1',3,180,'2026-11-08 12:03:01'),
    (4,102,'A2',2,150,'2026-11-08 11:58:00'),
    (5,102,'A2',3,NULL,'2026-11-08 12:03:00'),
    (6,103,'A3',2,150,'2026-11-08 11:55:00'),
    (7,103,'A3',2,180,'2026-11-08 11:56:00'),
    (8,103,'A3',3,120,'2026-11-08 12:03:00'),
    (9,104,'A4',1,NULL,'2026-11-08 11:50:00'),
    (10,104,'A4',1,NULL,'2026-11-08 11:50:01'),
    (11,105,'A5',1,120,'2026-11-08 11:50:00'),
    (12,105,'A5',1,120,'2026-11-08 11:50:01'),
    (13,106,'A6',1,100,'2026-11-08 11:50:00'),
    (14,106,'A6',2,150,'2026-11-08 11:58:00'),
    (15,106,'A6',3,120,'2026-11-08 12:03:00');

-- 1. Detect identical/repeated rows separately from same-version conflicts.
-- uniqExact excludes NULL values, so explicitly count its presence as a state.
SELECT trade_id, account_id, version, count() AS physical_rows,
       uniqExact(amount) AS distinct_non_null_amounts,
       toUInt8(countIf(isNull(amount)) > 0) AS null_state,
       uniqExact(amount) + toUInt8(countIf(isNull(amount)) > 0)
           AS distinct_amount_states,
       physical_rows > 1 AS repeated_version,
       distinct_amount_states > 1 AS conflicting_version
FROM lab04.raw_events
GROUP BY trade_id, account_id, version
ORDER BY trade_id, account_id, version;

-- 2. argMax(amount, version) can return an earlier non-null value.
-- The tuple preserves NULL in the latest row, but version ties still
-- have no guaranteed business tie-breaker.
SELECT trade_id, account_id,
       max(version) AS latest_version,
       argMax(amount, version) AS unsafe_latest_amount,
       argMax(tuple(version, amount), version) AS latest_row_preserving_null
FROM lab04.raw_events
GROUP BY trade_id, account_id
ORDER BY trade_id, account_id;
-- Trade 102 demonstrates the NULL trap (v2 150, v3 NULL).
-- Trade 101 demonstrates ambiguous tied max version (v3 NULL / v3 180).

-- 3. Show ONLY conflicts at maximum version, rather than historical conflicts.
WITH latest AS
(
    SELECT trade_id, account_id, max(version) AS latest_version
    FROM lab04.raw_events
    GROUP BY trade_id, account_id
),
per_version AS
(
    SELECT trade_id, account_id, version,
           uniqExact(amount) + toUInt8(countIf(isNull(amount)) > 0)
               AS distinct_amount_states
    FROM lab04.raw_events
    GROUP BY trade_id, account_id, version
)
SELECT p.trade_id, p.account_id, p.version, p.distinct_amount_states
FROM per_version AS p
INNER JOIN latest AS l
    ON p.trade_id = l.trade_id
   AND p.account_id = l.account_id
   AND p.version = l.latest_version
WHERE p.distinct_amount_states > 1
ORDER BY p.trade_id, p.account_id;
-- Trade 101 is conflicting at latest version; trade 103 is historical only.

-- 4. Filter by source-commit boundary FIRST, then choose the latest state.
SELECT trade_id, account_id,
       argMax(tuple(version, amount), version) AS state_as_of
FROM lab04.raw_events
WHERE trade_id = 106
  AND source_committed_at <= toDateTime64('2026-11-08 12:00:00', 3, 'UTC')
GROUP BY trade_id, account_id;
-- Expected: trade 106 -> (v2, amount 150), not v3 (amount 120).

-- 5. Current-state projection: FINAL is deduplication, not an audit log.
CREATE TABLE lab04.trades_current
(
    trade_id UInt64,
    account_id String,
    version UInt32,
    amount Nullable(Int64)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (trade_id, account_id);

INSERT INTO lab04.trades_current
SELECT trade_id, account_id, version, amount
FROM lab04.raw_events
ORDER BY ingest_id;

SELECT trade_id, account_id, version, amount
FROM lab04.trades_current FINAL
ORDER BY trade_id, account_id;
-- Version ties (trade 101) can produce either tied amount: do not assert
-- a deterministic winner. After merges, superseded rows may be gone.
-- To query historical states later, preserve lab04.raw_events (or an
-- equivalent immutable event log) with explicit retention and commit metadata.
