-- Session 02 fixture only. Does not modify the historical Session 01 seed.
-- Safe to run repeatedly: inserts use stable ingest_id and ON CONFLICT DO NOTHING.
-- This models PHYSICAL ingest rows, not unique logical trades.
CREATE SCHEMA IF NOT EXISTS lab02;

CREATE TABLE IF NOT EXISTS lab02.trade_versions (
    ingest_id BIGINT PRIMARY KEY,
    trade_id BIGINT NOT NULL,
    account_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    pnl NUMERIC(18, 4),
    status TEXT
);

INSERT INTO lab02.trade_versions
    (ingest_id, trade_id, account_id, version, event_time, ingested_at, pnl, status)
VALUES
    (1, 201, 'A1', 1, '2026-11-01 10:00:00+00', '2026-11-01 10:00:01+00',  5.0000, 'NEW'),
    (2, 201, 'A1', 2, '2026-11-01 10:01:00+00', '2026-11-01 10:01:02+00',  7.0000, 'FILLED'),
    (3, 201, 'A1', 2, '2026-11-01 10:01:00+00', '2026-11-01 10:01:05+00',  7.0000, 'FILLED'),
    (4, 202, 'A1', 1, '2026-11-01 10:03:00+00', '2026-11-01 10:03:01+00', -2.5000, 'NEW'),
    (5, 202, 'A1', 2, '2026-11-01 10:04:00+00', '2026-11-01 10:04:01+00', -1.5000, 'FILLED'),
    (6, 203, 'A2', 2, '2026-11-01 10:08:00+00', '2026-11-01 10:08:02+00',  9.0000, 'FILLED'),
    (7, 203, 'A2', 1, '2026-11-01 10:06:00+00', '2026-11-01 10:09:45+00',  1.0000, 'NEW'),
    (8, 204, 'A2', 1, '2026-11-01 10:10:00+00', '2026-11-01 10:10:04+00',     NULL, NULL),
    (9, 205, 'A3', 1, '2026-11-01 10:11:00+00', '2026-11-01 10:11:03+00',  4.0000, 'NEW'),
    (10,205, 'A3', 2, '2026-11-01 10:12:00+00', '2026-11-01 10:12:03+00',  8.0000, 'FILLED'),
    (11,205, 'A3', 2, '2026-11-01 10:12:00+00', '2026-11-01 10:12:06+00',  8.5000, 'FILLED'),
    (12,206, 'A3', 1, '2026-11-01 10:13:00+00', '2026-11-01 10:13:05+00',  0.0000, 'CANCELLED')
ON CONFLICT (ingest_id) DO NOTHING;

-- Input sanity only. Do not print a latest-version reference solution.
SELECT COUNT(*) AS physical_rows, COUNT(DISTINCT (trade_id, account_id)) AS logical_keys
FROM lab02.trade_versions;
