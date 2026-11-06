-- Session 02 / Task 2 — mentor walkthrough (NOT candidate-authored).
-- Policy: latest business version is authoritative; equal-version business-payload
-- differences mean conflict. ingestion metadata does not define business truth.
-- Any unresolved latest-version conflict blocks account PnL publication.
-- A FILLED trade with NULL PnL likewise blocks publication, but is a distinct
-- missing-value quality issue (not a same-version conflict).
-- Status: REFERENCE EXPLANATION, not executed against live PostgreSQL.

WITH latest_version AS (
    SELECT
        trade_id,
        account_id,
        MAX(version) AS version
    FROM lab02.trade_versions
    GROUP BY trade_id, account_id
),
latest_candidates AS (
    SELECT t.*
    FROM lab02.trade_versions AS t
    JOIN latest_version AS v
      USING (trade_id, account_id, version)
),
distinct_payloads AS (
    SELECT DISTINCT
        trade_id,
        account_id,
        event_time,
        status,
        pnl
    FROM latest_candidates
),
trade_conflicts AS (
    SELECT
        trade_id,
        account_id,
        COUNT(*) > 1 AS has_conflict
    FROM distinct_payloads
    GROUP BY trade_id, account_id
),
ranked AS (
    SELECT
        t.*,
        ROW_NUMBER() OVER (
            PARTITION BY trade_id, account_id
            ORDER BY version DESC, event_time DESC, ingest_id DESC
        ) AS rn
    FROM lab02.trade_versions AS t
),
account_aggregate AS (
    SELECT
        r.account_id,
        COUNT(*) FILTER (WHERE r.status = 'FILLED')
            AS filled_trade_count,
        SUM(r.pnl) FILTER (WHERE r.status = 'FILLED')
            AS computed_pnl,
        BOOL_OR(c.has_conflict)
            AS has_conflict,
        BOOL_OR(r.status = 'FILLED' AND r.pnl IS NULL)
            AS has_missing_filled_pnl
    FROM ranked AS r
    JOIN trade_conflicts AS c
      USING (trade_id, account_id)
    WHERE r.rn = 1
    GROUP BY r.account_id
)
SELECT
    account_id,
    filled_trade_count,
    CASE
        WHEN has_conflict OR has_missing_filled_pnl THEN NULL
        ELSE COALESCE(computed_pnl, 0::numeric)
    END AS total_pnl,
    has_conflict
FROM account_aggregate
ORDER BY account_id;

-- Fixture-derived expected account rows:
-- A1 | 2 | 5.5000 | false
-- A2 | 1 | 9.0000 | false
-- A3 | 1 | NULL   | true
--
-- Important limitations:
-- 1. Include event_time in conflict detection only if defined as an immutable
--    business payload attribute by the source contract.
-- 2. The representative status may be ambiguous when tied versions conflict.
--    This fixture has equal FILLED status for both rows of trade 205.
-- 3. Conservative fail-closed rule: any latest-version conflict for an account
--    blocks PnL, even if the conflicting trade currently appears non-FILLED.
--    A narrower "conflict impacts PnL" rule needs an explicit business contract.
-- 4. Accounts with zero FILLED trades receive 0::numeric if no DQ blockers.
-- 5. A separate DQ indicator for missing PnL should be added in production;
--    has_conflict is reserved for incompatible same-version business payloads.
