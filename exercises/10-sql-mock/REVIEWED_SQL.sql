-- Session A (Sessions 10 + 13), post-submission reviewed PostgreSQL reference.
-- Standalone SQL for the isolated lab10 fixture; NOT the original candidate attempt.
-- Run in one psql connection after postgres/fixtures/10-sql-mock.sql.
-- All comparisons use business key (trade_id, account_id); physical source/target
-- IDs and repeated deliveries are not unique logical trades.

-- A. Latest SOURCE trade state: exactly one row per valid business key.
-- Different payloads at the maximum version => ambiguous; identical replay
-- rows at that version do NOT create ambiguity.
CREATE OR REPLACE TEMP VIEW session10_source_latest AS
WITH valid_rows AS (
    SELECT src_id, trade_id, account_id, version, event_id, created_at, status, pnl
    FROM lab10.source_events
    WHERE trade_id IS NOT NULL
      AND NULLIF(BTRIM(account_id), '') IS NOT NULL
),
versioned AS (
    SELECT *,
           MAX(version) OVER (PARTITION BY trade_id, account_id) AS max_version
    FROM valid_rows
),
top_rows AS (
    SELECT *
    FROM versioned
    WHERE version = max_version
),
collapsed AS (
    SELECT trade_id,
           account_id,
           max_version AS latest_version,
           COUNT(DISTINCT ROW(status, pnl)) AS payload_variants,
           COUNT(DISTINCT event_id) AS event_variants,
           MIN(status) AS representative_status,
           MIN(pnl) AS representative_pnl,
           MIN(event_id) AS representative_event_id,
           MIN(created_at) AS latest_created_at,
           COUNT(*) AS latest_physical_rows
    FROM top_rows
    GROUP BY trade_id, account_id, max_version
)
SELECT trade_id,
       account_id,
       latest_version,
       CASE WHEN payload_variants = 1 THEN representative_status END AS latest_status,
       CASE WHEN payload_variants = 1 THEN representative_pnl END AS latest_pnl,
       (payload_variants > 1) AS is_ambiguous,
       CASE WHEN event_variants = 1 THEN representative_event_id END AS latest_event_id,
       latest_created_at,
       latest_physical_rows,
       event_variants
FROM collapsed;

-- Required output columns for Task A.
SELECT trade_id, account_id, latest_version, latest_status, latest_pnl, is_ambiguous
FROM session10_source_latest
ORDER BY account_id, trade_id;

-- Target is independently reduced BEFORE any source/target JOIN.
CREATE OR REPLACE TEMP VIEW session10_target_latest AS
WITH valid_rows AS (
    SELECT target_id, trade_id, account_id, version, event_id, available_at, status, pnl
    FROM lab10.target_events
    WHERE trade_id IS NOT NULL
      AND NULLIF(BTRIM(account_id), '') IS NOT NULL
),
versioned AS (
    SELECT *,
           MAX(version) OVER (PARTITION BY trade_id, account_id) AS max_version
    FROM valid_rows
),
top_rows AS (
    SELECT *
    FROM versioned
    WHERE version = max_version
),
collapsed AS (
    SELECT trade_id,
           account_id,
           max_version AS latest_version,
           COUNT(DISTINCT ROW(status, pnl)) AS payload_variants,
           COUNT(DISTINCT event_id) AS event_variants,
           MIN(status) AS representative_status,
           MIN(pnl) AS representative_pnl,
           MIN(event_id) AS representative_event_id,
           MIN(available_at) AS latest_available_at,
           COUNT(*) AS latest_physical_rows
    FROM top_rows
    GROUP BY trade_id, account_id, max_version
)
SELECT trade_id,
       account_id,
       latest_version,
       CASE WHEN payload_variants = 1 THEN representative_status END AS latest_status,
       CASE WHEN payload_variants = 1 THEN representative_pnl END AS latest_pnl,
       (payload_variants > 1) AS is_ambiguous,
       CASE WHEN event_variants = 1 THEN representative_event_id END AS latest_event_id,
       latest_available_at,
       latest_physical_rows,
       event_variants
FROM collapsed;

-- B. Logical-trade reconciliation: independent physical counts and state
-- aggregates prevent N x M join multiplication.
CREATE OR REPLACE TEMP VIEW session10_reconciliation AS
WITH source_counts AS (
    SELECT trade_id, account_id, COUNT(*)::bigint AS source_count
    FROM lab10.source_events
    WHERE trade_id IS NOT NULL AND NULLIF(BTRIM(account_id), '') IS NOT NULL
    GROUP BY trade_id, account_id
),
target_counts AS (
    SELECT trade_id, account_id, COUNT(*)::bigint AS target_count
    FROM lab10.target_events
    WHERE trade_id IS NOT NULL AND NULLIF(BTRIM(account_id), '') IS NOT NULL
    GROUP BY trade_id, account_id
),
paired AS (
    SELECT COALESCE(s.trade_id, t.trade_id) AS trade_id,
           COALESCE(s.account_id, t.account_id) AS account_id,
           COALESCE(sc.source_count, 0)::bigint AS source_count,
           COALESCE(tc.target_count, 0)::bigint AS target_count,
           s.latest_version AS source_latest_version,
           t.latest_version AS target_latest_version,
           CASE
               WHEN s.trade_id IS NULL THEN 'ORPHAN'
               WHEN t.trade_id IS NULL THEN 'MISSING'
               WHEN s.is_ambiguous OR t.is_ambiguous THEN 'AMBIGUOUS'
               WHEN t.latest_version < s.latest_version THEN 'STALE_TARGET'
               WHEN t.latest_version IS DISTINCT FROM s.latest_version
                 OR t.latest_status IS DISTINCT FROM s.latest_status
                 OR t.latest_pnl IS DISTINCT FROM s.latest_pnl
                 OR (s.latest_event_id IS NOT NULL AND t.latest_event_id IS NOT NULL
                     AND s.latest_event_id IS DISTINCT FROM t.latest_event_id)
                   THEN 'MISMATCH'
               ELSE 'MATCH'
           END AS dq_status
    FROM session10_source_latest s
    FULL JOIN session10_target_latest t
        ON s.trade_id = t.trade_id AND s.account_id = t.account_id
    LEFT JOIN source_counts sc
        ON sc.trade_id = s.trade_id AND sc.account_id = s.account_id
    LEFT JOIN target_counts tc
        ON tc.trade_id = t.trade_id AND tc.account_id = t.account_id
)
SELECT trade_id,
       account_id,
       source_count,
       target_count,
       source_latest_version,
       target_latest_version,
       (dq_status <> 'MATCH') AS has_mismatch,
       dq_status
FROM paired;

-- Required output columns for Task B.
SELECT trade_id, account_id, source_count, target_count,
       source_latest_version, target_latest_version, has_mismatch, dq_status
FROM session10_reconciliation
ORDER BY account_id, trade_id;

-- Invalid business keys are reported by physical row ID, NEVER joined as NULL=NULL.
SELECT 'source' AS side, src_id AS physical_row_id, trade_id, account_id,
       'INVALID_BUSINESS_KEY' AS dq_rule
FROM lab10.source_events
WHERE trade_id IS NULL OR NULLIF(BTRIM(account_id), '') IS NULL
UNION ALL
SELECT 'target' AS side, target_id AS physical_row_id, trade_id, account_id,
       'INVALID_BUSINESS_KEY' AS dq_rule
FROM lab10.target_events
WHERE trade_id IS NULL OR NULLIF(BTRIM(account_id), '') IS NULL
ORDER BY side, physical_row_id;

-- C. SLA: first query-visible EXACT latest source event state in the target.
-- This is a fresh as-of computation (no future source/target versions leak in).
-- Evaluation cutoff: 2026-11-08 13:30:00+00; 95% within 10 minutes.
-- Mature eligibility uses source created_at <= as_of - 10 minutes.
-- A source max-version event identity/payload conflict is UNKNOWN.
-- A nonmatching/absent persisted target latest event after maturity is MISSING.
-- An incomplete earlier history remains a separate event-level DQ concern.
CREATE OR REPLACE TEMP VIEW session10_sla_report AS
WITH settings AS (
    SELECT TIMESTAMPTZ '2026-11-08 13:30:00+00' AS as_of,
           INTERVAL '10 minutes' AS objective,
           95::numeric AS required_pct
),
source_asof AS (
    SELECT se.*,
           MAX(version) OVER (PARTITION BY trade_id, account_id) AS max_version
    FROM lab10.source_events se
    CROSS JOIN settings p
    WHERE se.trade_id IS NOT NULL
      AND NULLIF(BTRIM(se.account_id), '') IS NOT NULL
      AND se.created_at <= p.as_of
),
latest_source AS (
    SELECT trade_id, account_id, max_version AS latest_version,
           COUNT(DISTINCT ROW(event_id, status, pnl)) AS state_variants,
           MIN(event_id) AS latest_event_id,
           MIN(status) AS latest_status,
           MIN(pnl) AS latest_pnl,
           MIN(created_at) AS latest_created_at
    FROM source_asof
    WHERE version = max_version
    GROUP BY trade_id, account_id, max_version
),
eligible AS (
    SELECT s.*, p.as_of, p.objective, p.required_pct
    FROM latest_source s
    CROSS JOIN settings p
    WHERE s.latest_created_at <= p.as_of - p.objective
),
visible AS (
    SELECT e.trade_id, e.account_id,
           MIN(t.available_at) AS first_visible_at
    FROM eligible e
    LEFT JOIN lab10.target_events t
      ON e.state_variants = 1
     AND t.trade_id = e.trade_id
     AND t.account_id = e.account_id
     AND t.version = e.latest_version
     AND t.event_id = e.latest_event_id
     AND t.status IS NOT DISTINCT FROM e.latest_status
     AND t.pnl IS NOT DISTINCT FROM e.latest_pnl
     AND t.available_at <= e.as_of
    GROUP BY e.trade_id, e.account_id
),
classified AS (
    SELECT e.trade_id, e.account_id,
           CASE
               WHEN e.state_variants <> 1 THEN 'UNKNOWN'
               WHEN v.first_visible_at IS NULL THEN 'MISSING'
               WHEN v.first_visible_at <= e.latest_created_at + e.objective THEN 'ON_TIME'
               ELSE 'LATE'
           END AS outcome,
           e.required_pct
    FROM eligible e
    JOIN visible v USING (trade_id, account_id)
),
totals AS (
    SELECT COUNT(*)::bigint AS eligible_count,
           COUNT(*) FILTER (WHERE outcome = 'ON_TIME')::bigint AS on_time_count,
           COUNT(*) FILTER (WHERE outcome = 'LATE')::bigint AS late_count,
           COUNT(*) FILTER (WHERE outcome = 'MISSING')::bigint AS missing_count,
           COUNT(*) FILTER (WHERE outcome = 'UNKNOWN')::bigint AS unknown_count,
           COALESCE(MAX(required_pct), 95::numeric) AS required_pct
    FROM classified
)
SELECT eligible_count, on_time_count, late_count, missing_count,
       ROUND(100.0 * on_time_count / NULLIF(eligible_count, 0), 2) AS on_time_pct,
       CASE
           WHEN eligible_count = 0 THEN NULL::boolean
           WHEN 100.0 * on_time_count / eligible_count >= required_pct THEN TRUE
           WHEN 100.0 * (on_time_count + unknown_count) / eligible_count < required_pct THEN FALSE
           ELSE NULL::boolean
       END AS sla_met,
       unknown_count,
       ROUND(100.0 * (on_time_count + unknown_count) / NULLIF(eligible_count, 0), 2)
           AS on_time_pct_upper
FROM totals;

-- Required output columns for Task C.
-- NULL sla_met means INDETERMINATE and MUST NOT be mapped to CI PASS.
SELECT eligible_count, on_time_count, late_count, missing_count,
       on_time_pct, sla_met
FROM session10_sla_report;
