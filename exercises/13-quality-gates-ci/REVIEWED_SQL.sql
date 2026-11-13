-- Session A / Session 13: post-review SQL diagnostics for the isolated PostgreSQL
-- lab10 fixture. This is a synthetic training gate, not the unified Kafka/Flink
-- integration or a sink-side completion barrier.
-- Source/target rows are first reduced independently by immutable event_id.
-- The baseline lab10 fixture intentionally includes DQ violations: the final
-- blocking assertion SHOULD return a nonzero exit status with ON_ERROR_STOP=1.

CREATE OR REPLACE TEMP VIEW session13_event_diagnostics AS
WITH source_events AS (
    SELECT event_id,
           COUNT(*)::bigint AS source_physical_rows,
           COUNT(DISTINCT ROW(trade_id, account_id, version, pnl, status)) AS source_payload_variants,
           BOOL_OR(trade_id IS NULL OR NULLIF(BTRIM(account_id), '') IS NULL) AS source_invalid_key,
           MIN(trade_id) AS source_trade_id,
           MIN(account_id) AS source_account_id,
           MIN(version) AS source_version,
           MIN(pnl) AS source_pnl,
           MIN(status) AS source_status
    FROM lab10.source_events
    GROUP BY event_id
),
target_events AS (
    SELECT event_id,
           COUNT(*)::bigint AS target_physical_rows,
           COUNT(DISTINCT ROW(trade_id, account_id, version, pnl, status)) AS target_payload_variants,
           BOOL_OR(trade_id IS NULL OR NULLIF(BTRIM(account_id), '') IS NULL) AS target_invalid_key,
           MIN(trade_id) AS target_trade_id,
           MIN(account_id) AS target_account_id,
           MIN(version) AS target_version,
           MIN(pnl) AS target_pnl,
           MIN(status) AS target_status
    FROM lab10.target_events
    GROUP BY event_id
)
SELECT COALESCE(s.event_id, t.event_id) AS event_id,
       s.source_trade_id AS source_trade_id,
       s.source_account_id AS source_account_id,
       t.target_trade_id AS target_trade_id,
       t.target_account_id AS target_account_id,
       COALESCE(s.source_physical_rows, 0)::bigint AS source_physical_rows,
       COALESCE(t.target_physical_rows, 0)::bigint AS target_physical_rows,
       CASE
           WHEN s.event_id IS NULL THEN 'UNEXPECTED_EVENT'
           WHEN t.event_id IS NULL THEN 'MISSING_EVENT'
           WHEN s.source_invalid_key OR t.target_invalid_key THEN 'INVALID_BUSINESS_KEY'
           WHEN s.source_payload_variants > 1 OR t.target_payload_variants > 1
                THEN 'EVENT_ID_PAYLOAD_CONFLICT'
           WHEN s.source_trade_id IS DISTINCT FROM t.target_trade_id
             OR s.source_account_id IS DISTINCT FROM t.target_account_id
             OR s.source_version IS DISTINCT FROM t.target_version
             OR s.source_pnl IS DISTINCT FROM t.target_pnl
             OR s.source_status IS DISTINCT FROM t.target_status
                THEN 'PAYLOAD_MISMATCH'
           ELSE 'MATCH'
       END AS dq_rule
FROM source_events s
FULL JOIN target_events t USING (event_id);

-- Event-set membership, multiplicity and precise anomalies.
SELECT event_id, source_trade_id, source_account_id,
       target_trade_id, target_account_id,
       source_physical_rows, target_physical_rows, dq_rule
FROM session13_event_diagnostics
ORDER BY dq_rule, event_id;

-- In this isolated fixture, the independent plan expects 12 source physical
-- rows. Do NOT derive the expected total from the target or from an empty
-- observed source result. For the unified streaming lab, use the sealed
-- PostgreSQL source batch manifest instead of this fixed training constant.
CREATE OR REPLACE TEMP VIEW session13_gate_summary AS
WITH plan AS (
    SELECT 12::bigint AS expected_source_physical_rows
),
observed AS (
    SELECT COUNT(*)::bigint AS observed_source_physical_rows
    FROM lab10.source_events
),
issues AS (
    SELECT COUNT(*) FILTER (WHERE dq_rule <> 'MATCH')::bigint AS issue_count,
           COUNT(*) FILTER (WHERE dq_rule = 'MISSING_EVENT')::bigint AS missing_event_count,
           COUNT(*) FILTER (WHERE dq_rule = 'UNEXPECTED_EVENT')::bigint AS unexpected_event_count,
           COUNT(*) FILTER (WHERE dq_rule = 'PAYLOAD_MISMATCH')::bigint AS payload_mismatch_count,
           COUNT(*) FILTER (WHERE dq_rule = 'INVALID_BUSINESS_KEY')::bigint AS invalid_key_count,
           COUNT(*) FILTER (WHERE dq_rule = 'EVENT_ID_PAYLOAD_CONFLICT')::bigint
               AS event_identity_conflict_count
    FROM session13_event_diagnostics
)
SELECT plan.expected_source_physical_rows,
       observed.observed_source_physical_rows,
       issues.*,
       CASE
           WHEN plan.expected_source_physical_rows IS NULL THEN 'INDETERMINATE'
           WHEN observed.observed_source_physical_rows <> plan.expected_source_physical_rows THEN 'FAIL'
           WHEN observed.observed_source_physical_rows = 0 THEN 'FAIL'
           WHEN issues.issue_count > 0 THEN 'FAIL'
           ELSE 'PASS'
       END AS gate_status
FROM plan CROSS JOIN observed CROSS JOIN issues;

SELECT * FROM session13_gate_summary;

-- Deliberate blocking negative control. The provided fixture is NOT clean:
-- missing/extra events, payload mismatches and invalid business keys exist.
-- Run with psql -v ON_ERROR_STOP=1 to propagate failure to CI.
DO $quality_gate$
DECLARE
    gate RECORD;
BEGIN
    SELECT * INTO STRICT gate FROM session13_gate_summary;
    IF gate.gate_status <> 'PASS' THEN
        RAISE EXCEPTION 'Session 13 DQ gate blocked: %, observed/expected=%/%, issues=%, missing=%, extra=%, mismatched=%',
            gate.gate_status,
            gate.observed_source_physical_rows,
            gate.expected_source_physical_rows,
            gate.issue_count,
            gate.missing_event_count,
            gate.unexpected_event_count,
            gate.payload_mismatch_count;
    END IF;
END
$quality_gate$;

-- SQL alone cannot prove that pytest collected/ran mandatory suites, that
-- a Kafka consumer's zero lag means ClickHouse durability, or that a source
-- manifest was sealed. These require independent non-SQL CI/streaming evidence.
