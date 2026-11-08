-- PostgreSQL reconciliation on exported snapshots. The independent inputs are
-- reduced to exactly one row per VALID composite business key before FULL JOIN.
-- Note: "duplicate" means repeated (trade_id, account_id, version); mere
-- presence of several DIFFERENT versions is expected state history.
CREATE OR REPLACE VIEW lab04.invalid_keys AS
SELECT 'SOURCE'::TEXT AS side, src_id AS physical_id,
       trade_id, account_id, 'INVALID_KEY'::TEXT AS anomaly
FROM lab04.source_snapshot
WHERE trade_id IS NULL OR account_id IS NULL
UNION ALL
SELECT 'TARGET'::TEXT, record_id, trade_id, account_id, 'INVALID_KEY'::TEXT
FROM lab04.target_snapshot
WHERE trade_id IS NULL OR account_id IS NULL;

CREATE OR REPLACE VIEW lab04.reconciliation_report AS
WITH
source_valid AS (
  SELECT * FROM lab04.source_snapshot
  WHERE trade_id IS NOT NULL AND account_id IS NOT NULL
),
target_valid AS (
  SELECT * FROM lab04.target_snapshot
  WHERE trade_id IS NOT NULL AND account_id IS NOT NULL
),
source_counts AS (
  SELECT trade_id, account_id,
         COUNT(*) AS source_count,
         BOOL_OR(amount IS NULL) AS source_has_null_amount
  FROM source_valid GROUP BY trade_id, account_id
),
target_counts AS (
  SELECT trade_id, account_id,
         COUNT(*) AS target_count,
         BOOL_OR(amount IS NULL) AS target_has_null_amount,
         COALESCE(BOOL_OR(status = 'FAILED'), FALSE) AS has_failed,
         BOOL_OR(status IS NULL OR status NOT IN ('SUCCESS','FAILED'))
             AS has_unknown_status
  FROM target_valid GROUP BY trade_id, account_id
),
source_versions AS (
  SELECT trade_id, account_id, version, COUNT(*) AS version_rows,
         COUNT(DISTINCT amount)
           + CASE WHEN BOOL_OR(amount IS NULL) THEN 1 ELSE 0 END
           AS amount_states,
         MIN(amount) AS representative_amount
  FROM source_valid GROUP BY trade_id, account_id, version
),
target_versions AS (
  SELECT trade_id, account_id, version, COUNT(*) AS version_rows,
         COUNT(DISTINCT amount)
           + CASE WHEN BOOL_OR(amount IS NULL) THEN 1 ELSE 0 END
           AS amount_states,
         MIN(amount) AS representative_amount
  FROM target_valid GROUP BY trade_id, account_id, version
),
source_max AS (
  SELECT trade_id, account_id, MAX(version) AS source_version
  FROM source_versions GROUP BY trade_id, account_id
),
target_max AS (
  SELECT trade_id, account_id, MAX(version) AS target_version
  FROM target_versions GROUP BY trade_id, account_id
),
source_state AS (
  SELECT v.trade_id, v.account_id, m.source_version,
         BOOL_OR(v.version_rows > 1) AS source_duplicate,
         BOOL_OR(v.amount_states > 1) AS source_conflicting_version,
         BOOL_OR(v.amount_states > 1 AND v.version < m.source_version)
           AS source_historical_conflict,
         MAX(v.amount_states) FILTER (WHERE v.version=m.source_version)
           AS source_latest_amount_states,
         MAX(v.representative_amount) FILTER (WHERE v.version=m.source_version)
           AS source_amount
  FROM source_versions v
  JOIN source_max m USING (trade_id, account_id)
  GROUP BY v.trade_id, v.account_id, m.source_version
),
target_state AS (
  SELECT v.trade_id, v.account_id, m.target_version,
         BOOL_OR(v.version_rows > 1) AS target_duplicate,
         BOOL_OR(v.amount_states > 1) AS target_conflicting_version,
         BOOL_OR(v.amount_states > 1 AND v.version < m.target_version)
           AS target_historical_conflict,
         MAX(v.amount_states) FILTER (WHERE v.version=m.target_version)
           AS target_latest_amount_states,
         MAX(v.representative_amount) FILTER (WHERE v.version=m.target_version)
           AS target_amount
  FROM target_versions v
  JOIN target_max m USING (trade_id, account_id)
  GROUP BY v.trade_id, v.account_id, m.target_version
)
SELECT
  COALESCE(s.trade_id,t.trade_id) AS trade_id,
  COALESCE(s.account_id,t.account_id) AS account_id,
  COALESCE(s.source_count,0) AS source_count,
  COALESCE(t.target_count,0) AS target_count,
  (s.trade_id IS NOT NULL AND t.trade_id IS NULL) AS is_missing,
  (s.trade_id IS NULL AND t.trade_id IS NOT NULL) AS is_orphan,
  COALESCE(ss.source_duplicate,FALSE) AS source_duplicate,
  COALESCE(ts.target_duplicate,FALSE) AS target_duplicate,
  COALESCE(t.has_failed,FALSE) AS has_failed,
  COALESCE(t.has_unknown_status,FALSE) AS has_unknown_status,
  COALESCE(s.source_has_null_amount,FALSE)
    OR COALESCE(t.target_has_null_amount,FALSE) AS has_null_amount,
  COALESCE(ss.source_conflicting_version,FALSE)
    OR COALESCE(ts.target_conflicting_version,FALSE) AS has_conflicting_version,
  COALESCE(ss.source_historical_conflict,FALSE)
    OR COALESCE(ts.target_historical_conflict,FALSE) AS has_historical_conflict,
  COALESCE(ss.source_latest_amount_states > 1,FALSE)
    OR COALESCE(ts.target_latest_amount_states > 1,FALSE) AS has_latest_conflict,
  ss.source_version, ts.target_version,
  ss.source_amount, ts.target_amount,
  (ss.source_version IS NOT NULL AND ts.target_version IS NOT NULL
    AND ss.source_version > ts.target_version) AS missing_update,
  (ss.source_version IS NOT NULL AND ts.target_version IS NOT NULL
    AND ss.source_version < ts.target_version) AS target_ahead,
  CASE
    WHEN ss.source_version IS NULL OR ts.target_version IS NULL THEN NULL::BOOLEAN
    WHEN ss.source_version <> ts.target_version THEN NULL::BOOLEAN
    WHEN ss.source_latest_amount_states <> 1
      OR ts.target_latest_amount_states <> 1 THEN NULL::BOOLEAN
    ELSE ss.source_amount IS DISTINCT FROM ts.target_amount
  END AS amount_mismatch
FROM source_counts s
FULL OUTER JOIN target_counts t
  ON s.trade_id=t.trade_id AND s.account_id=t.account_id
LEFT JOIN source_state ss
  ON ss.trade_id=s.trade_id AND ss.account_id=s.account_id
LEFT JOIN target_state ts
  ON ts.trade_id=t.trade_id AND ts.account_id=t.account_id;
