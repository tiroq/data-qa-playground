-- Executed automatically on FIRST initialization of an empty ClickHouse volume.
-- DO NOT rerun this INSERT file directly against a populated database.
-- Read clickhouse/README.md for a deliberate reset/reseed procedure.
-- The 6-row case matches Session 03 interview question.
INSERT INTO lab03.trading_events
    (ingest_id, account_id, trade_id, version, trade_date, event_time, ingested_at, pnl, status)
VALUES
    (1, 'A1', 'T100', 1, '2026-11-06', '2026-11-06 10:00:00', '2026-11-06 10:00:01', 10.0000, 'NEW'),
    (2, 'A1', 'T100', 2, '2026-11-06', '2026-11-06 10:01:00', '2026-11-06 10:01:02',  7.0000, 'FILLED'),
    (3, 'A1', 'T100', 2, '2026-11-06', '2026-11-06 10:01:00', '2026-11-06 10:01:05',  7.0000, 'FILLED'),
    (4, 'A1', 'T101', 1, '2026-11-06', '2026-11-06 10:03:00', '2026-11-06 10:03:01', -2.0000, 'FILLED'),
    (5, 'A2', 'T200', 1, '2026-11-06', '2026-11-06 10:05:00', '2026-11-06 10:05:01',  3.0000, 'NEW'),
    (6, 'A2', 'T200', 2, '2026-11-06', '2026-11-06 10:06:00', '2026-11-06 10:06:02',  1.0000, 'FILLED');

-- Mirrors postgres/fixtures/02-trade-versions.sql one-to-one by ingest_id.
-- Includes duplicate delivery, out-of-order ingest, NULLs, and a conflicting
-- same-version payload. The conflicting payload is intentionally NOT resolved.
INSERT INTO lab03.trade_versions
    (ingest_id, trade_id, account_id, version, event_time, ingested_at, pnl, status)
VALUES
    (1, 201, 'A1', 1, '2026-11-01 10:00:00', '2026-11-01 10:00:01',  5.0000, 'NEW'),
    (2, 201, 'A1', 2, '2026-11-01 10:01:00', '2026-11-01 10:01:02',  7.0000, 'FILLED'),
    (3, 201, 'A1', 2, '2026-11-01 10:01:00', '2026-11-01 10:01:05',  7.0000, 'FILLED'),
    (4, 202, 'A1', 1, '2026-11-01 10:03:00', '2026-11-01 10:03:01', -2.5000, 'NEW'),
    (5, 202, 'A1', 2, '2026-11-01 10:04:00', '2026-11-01 10:04:01', -1.5000, 'FILLED'),
    (6, 203, 'A2', 2, '2026-11-01 10:08:00', '2026-11-01 10:08:02',  9.0000, 'FILLED'),
    (7, 203, 'A2', 1, '2026-11-01 10:06:00', '2026-11-01 10:09:45',  1.0000, 'NEW'),
    (8, 204, 'A2', 1, '2026-11-01 10:10:00', '2026-11-01 10:10:04',     NULL, NULL),
    (9, 205, 'A3', 1, '2026-11-01 10:11:00', '2026-11-01 10:11:03',  4.0000, 'NEW'),
    (10,205, 'A3', 2, '2026-11-01 10:12:00', '2026-11-01 10:12:03',  8.0000, 'FILLED'),
    (11,205, 'A3', 2, '2026-11-01 10:12:00', '2026-11-01 10:12:06',  8.5000, 'FILLED'),
    (12,206, 'A3', 1, '2026-11-01 10:13:00', '2026-11-01 10:13:05',  0.0000, 'CANCELLED');
