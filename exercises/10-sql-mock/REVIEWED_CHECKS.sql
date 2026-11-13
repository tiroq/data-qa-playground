-- SQL regression assertions for the reviewed Session 10 reference.
-- Prerequisite: execute REVIEWED_SQL.sql in the SAME psql connection first.
-- The tests use only the isolated lab10 fixture. Changes are rolled back.
-- Example from repository root:
-- cat exercises/10-sql-mock/REVIEWED_SQL.sql \
--     exercises/10-sql-mock/REVIEWED_CHECKS.sql \
--   | docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1

DO $baseline$
BEGIN
    IF (SELECT COUNT(*) FROM session10_source_latest) <> 9 THEN
        RAISE EXCEPTION 'Expected 9 valid source business keys';
    END IF;
    IF (SELECT COUNT(*) FROM session10_reconciliation) <> 11 THEN
        RAISE EXCEPTION 'Expected 11 source/target business keys';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_source_latest
        WHERE trade_id = 304 AND account_id = 'A2'
          AND latest_version = 2 AND NOT is_ambiguous
          AND latest_pnl = 4::numeric AND latest_physical_rows = 2
    ) THEN
        RAISE EXCEPTION 'Identical latest-version replay must collapse to one state';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 304 AND account_id = 'A2'
          AND source_count = 2 AND target_count = 2
          AND dq_status = 'MATCH'
    ) THEN
        RAISE EXCEPTION 'Physical duplicate must not inflate JOIN cardinality';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 305 AND account_id = 'A3' AND dq_status = 'MISMATCH'
    ) THEN
        RAISE EXCEPTION 'Changed PnL must be MISMATCH';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 308 AND account_id = 'A4' AND dq_status = 'STALE_TARGET'
    ) THEN
        RAISE EXCEPTION 'Old target version must be STALE_TARGET';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 307 AND account_id = 'A4' AND dq_status = 'MISSING'
    ) OR NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 307 AND account_id = 'A999' AND dq_status = 'ORPHAN'
    ) THEN
        RAISE EXCEPTION 'Missing and orphan account keys must remain distinct';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM session10_sla_report
        WHERE eligible_count = 9 AND on_time_count = 5
          AND late_count = 1 AND missing_count = 3
          AND unknown_count = 0
          AND on_time_pct = 55.56 AND sla_met IS FALSE
    ) THEN
        RAISE EXCEPTION 'SLA cutoff / denominator / first matching state is wrong';
    END IF;
END
$baseline$;

BEGIN;

-- Separate event_id but contradictory PnL on the same max version.
INSERT INTO lab10.source_events
    (src_id, trade_id, account_id, version, event_id, created_at, pnl, status)
VALUES
    (9001, 301, 'A1', 2, 'S301-2-CONFLICT',
     TIMESTAMPTZ '2026-11-08 12:01:00+00', 999, 'FILLED');

DO $same_version$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM session10_source_latest
        WHERE trade_id = 301 AND account_id = 'A1'
          AND is_ambiguous AND latest_status IS NULL AND latest_pnl IS NULL
    ) OR NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 301 AND account_id = 'A1' AND dq_status = 'AMBIGUOUS'
    ) THEN
        RAISE EXCEPTION 'Conflicting maximum version must never choose an arbitrary PnL';
    END IF;
END
$same_version$;

ROLLBACK;

BEGIN;

-- SQL NULL is a valid unknown PnL, not equivalent to numeric zero.
INSERT INTO lab10.source_events
    (src_id, trade_id, account_id, version, event_id, created_at, pnl, status)
VALUES
    (9002, 320, 'A_TEST', 1, 'S320-1',
     TIMESTAMPTZ '2026-11-08 12:00:00+00', NULL, 'FILLED');
INSERT INTO lab10.target_events
    (target_id, trade_id, account_id, version, event_id, available_at, pnl, status)
VALUES
    (9902, 320, 'A_TEST', 1, 'S320-1',
     TIMESTAMPTZ '2026-11-08 12:01:00+00', NULL, 'FILLED');

DO $null_payload$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM session10_source_latest
        WHERE trade_id = 320 AND account_id = 'A_TEST'
          AND NOT is_ambiguous AND latest_pnl IS NULL
    ) OR NOT EXISTS (
        SELECT 1 FROM session10_reconciliation
        WHERE trade_id = 320 AND account_id = 'A_TEST' AND dq_status = 'MATCH'
    ) THEN
        RAISE EXCEPTION 'NULL PnL equality failed';
    END IF;
END
$null_payload$;

INSERT INTO lab10.source_events
    (src_id, trade_id, account_id, version, event_id, created_at, pnl, status)
VALUES
    (9003, 320, 'A_TEST', 1, 'S320-1-DIFFERENT',
     TIMESTAMPTZ '2026-11-08 12:00:00+00', 0, 'FILLED');

DO $null_vs_zero$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM session10_source_latest
        WHERE trade_id = 320 AND account_id = 'A_TEST' AND is_ambiguous
    ) THEN
        RAISE EXCEPTION 'NULL vs zero PnL must be different max-version payloads';
    END IF;
END
$null_vs_zero$;

ROLLBACK;

SELECT 'Session 10 reviewed SQL baseline and negative controls passed' AS result;
