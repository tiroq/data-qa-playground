-- Session 04: PostgreSQL discussion examples / inspection queries.
-- Requires sql/01-fixture.sql and sql/02-reconciliation.sql.
-- These are mentor-authored examples, NOT a candidate's unaided SQL attempt.
-- Safe to re-run: SELECT-only, no schema/data modification.

-- 1. Source counts BEFORE joining target, at the true business grain.
SELECT trade_id, account_id, COUNT(*) AS source_count
FROM lab04.source_snapshot
WHERE trade_id IS NOT NULL AND account_id IS NOT NULL
GROUP BY trade_id, account_id
ORDER BY trade_id, account_id;

-- 2. Independent target status flags. Never group by status itself.
-- BOOL_OR(FALSE, NULL) is FALSE; BOOL_OR(NULL, NULL) is NULL.
SELECT trade_id, account_id, COUNT(*) AS target_count,
       COALESCE(BOOL_OR(status = 'FAILED'), FALSE) AS has_failed,
       BOOL_OR(status IS NULL OR status NOT IN ('SUCCESS', 'FAILED'))
           AS has_unknown_status
FROM lab04.target_snapshot
WHERE trade_id IS NOT NULL AND account_id IS NOT NULL
GROUP BY trade_id, account_id
ORDER BY trade_id, account_id;

-- 3. Source/target invalid business keys are quarantined, not MISSING/ORPHAN.
SELECT *
FROM lab04.invalid_keys
ORDER BY side, physical_id;

-- 4. Full report: physical rows + independent latest-version diagnostics.
SELECT trade_id, account_id, source_count, target_count,
       is_missing, is_orphan, source_duplicate, target_duplicate,
       has_failed, has_unknown_status, has_null_amount,
       source_version, target_version, missing_update, target_ahead,
       has_conflicting_version, has_historical_conflict,
       has_latest_conflict, amount_mismatch
FROM lab04.reconciliation_report
ORDER BY trade_id, account_id;

-- 5. Same-version conflicting amounts, treating NULL as its own state.
-- Two NULLs: one state (not conflicting); NULL and 120: two states.
SELECT trade_id, account_id, version,
       COUNT(*) AS physical_rows,
       COUNT(DISTINCT amount)
         + CASE WHEN BOOL_OR(amount IS NULL) THEN 1 ELSE 0 END
           AS distinct_amount_states
FROM lab04.target_snapshot
WHERE trade_id IS NOT NULL AND account_id IS NOT NULL
GROUP BY trade_id, account_id, version
HAVING COUNT(DISTINCT amount)
         + CASE WHEN BOOL_OR(amount IS NULL) THEN 1 ELSE 0 END > 1
ORDER BY trade_id, account_id, version;

-- 6. Point-in-time current state: FILTER FIRST, pick latest version AFTER.
-- Sample history is inline because lab04 snapshots intentionally don't
-- claim they have source-commit metadata.
WITH trade_events (trade_id, account_id, version, amount, source_committed_at) AS (
    VALUES
      (101::BIGINT, 'A1'::TEXT, 1, 100::NUMERIC,
       TIMESTAMPTZ '2026-11-08 11:50:00+00'),
      (101, 'A1', 2, 150, TIMESTAMPTZ '2026-11-08 11:58:00+00'),
      (101, 'A1', 3, 120, TIMESTAMPTZ '2026-11-08 12:03:00+00')
),
eligible AS (
    SELECT * FROM trade_events
    WHERE source_committed_at <= TIMESTAMPTZ '2026-11-08 12:00:00+00'
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY trade_id, account_id
        ORDER BY version DESC, source_committed_at DESC
    ) AS rn
    FROM eligible
)
SELECT trade_id, account_id, version, amount, source_committed_at
FROM ranked WHERE rn = 1;
-- Expected: trade=101, version=2, amount=150.
-- ROW_NUMBER is not a data-quality conflict detector: separately inspect
-- equal-key/equal-version conflicting payloads before accepting selected row.

-- 7. Why matched aggregate amount is NOT enough for daily PnL reconciliation.
-- Assume exactly 10 FILLED latest-state trades, including one invalid NULL.
-- Eight pnl=100, one pnl=0, and one NULL -> known sum = 800.
WITH latest_trades AS (
    SELECT n AS trade_id, 'A1'::TEXT AS account_id,
           1 AS version, 'FILLED'::TEXT AS status,
           CASE
             WHEN n = 10 THEN NULL::NUMERIC
             WHEN n = 9 THEN 0::NUMERIC
             ELSE 100::NUMERIC
           END AS pnl
    FROM generate_series(1, 10) AS n
),
expected AS (
    SELECT account_id,
           COUNT(*) AS eligible_trades,
           COUNT(pnl) AS valid_pnl_count,
           COUNT(*) - COUNT(pnl) AS invalid_pnl_count,
           SUM(pnl) AS known_pnl_sum
    FROM latest_trades
    WHERE status = 'FILLED'
    GROUP BY account_id
),
target_daily AS (
    SELECT 'A1'::TEXT AS account_id, 800::NUMERIC AS stored_daily_pnl
)
SELECT e.account_id, e.eligible_trades, e.valid_pnl_count,
       e.invalid_pnl_count, e.known_pnl_sum, t.stored_daily_pnl,
       (e.known_pnl_sum IS NOT DISTINCT FROM t.stored_daily_pnl)
          AS amount_matches,
       (e.invalid_pnl_count = 0) AS aggregate_complete,
       (e.invalid_pnl_count = 0
        AND e.known_pnl_sum IS NOT DISTINCT FROM t.stored_daily_pnl)
          AS reconciliation_pass
FROM expected e
JOIN target_daily t USING (account_id);
-- Expected: amount_matches=true, aggregate_complete=false,
-- reconciliation_pass=false. Other defects (missing trades, versions,
-- unknown status, historical conflict) require separate independent flags.
