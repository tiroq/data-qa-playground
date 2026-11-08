-- Run AFTER 01-fixture.sql, 02-reconciliation.sql and 03-sla.sql.
-- Fail on broken or empty results instead of printing a misleading PASS.
DO $$
BEGIN
 IF (SELECT COUNT(*) FROM lab04.reconciliation_report) <> 14 THEN
   RAISE EXCEPTION 'Expected 14 valid business keys in reconciliation';
 END IF;
 IF EXISTS (
   SELECT 1 FROM lab04.reconciliation_report
   GROUP BY trade_id, account_id HAVING COUNT(*) <> 1
 ) THEN
   RAISE EXCEPTION 'JOIN cardinality multiplication detected';
 END IF;
 IF (SELECT SUM(source_count) FROM lab04.reconciliation_report) <> 15 OR
    (SELECT SUM(target_count) FROM lab04.reconciliation_report) <> 17 THEN
   RAISE EXCEPTION 'Physical source/target counts changed after aggregation/JOIN';
 END IF;
 IF (SELECT COUNT(*) FROM lab04.invalid_keys) <> 3 THEN
   RAISE EXCEPTION 'Expected three quarantined null business keys';
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=101
    AND account_id='A1' AND source_count=2 AND target_count=2
    AND source_duplicate AND target_duplicate
    AND NOT is_missing AND NOT is_orphan
 ) THEN RAISE EXCEPTION 'Duplicate on both sides test failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=102
     AND account_id='A1' AND is_missing AND target_count=0
 ) THEN RAISE EXCEPTION 'MISSING classification failed'; END IF;
 IF (SELECT COUNT(*) FROM lab04.reconciliation_report WHERE is_orphan) <> 2 THEN
   RAISE EXCEPTION 'ORPHAN classification failed';
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=103
     AND account_id='A2' AND amount_mismatch IS TRUE
 ) THEN RAISE EXCEPTION 'Same-version amount mismatch test failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=105
     AND account_id='A3' AND has_null_amount AND amount_mismatch IS FALSE
 ) THEN RAISE EXCEPTION 'NULL vs NULL must not be amount mismatch'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=106
     AND account_id='A3' AND has_failed AND NOT is_missing
 ) THEN RAISE EXCEPTION 'FAILED physical target must not be missing'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=107
     AND account_id='A4' AND has_unknown_status
 ) THEN RAISE EXCEPTION 'Unknown status test failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=108
     AND account_id='A5' AND missing_update AND amount_mismatch IS NULL
 ) THEN RAISE EXCEPTION 'Missing latest version must not imply amount mismatch'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=110
     AND account_id='A6' AND target_ahead
 ) THEN RAISE EXCEPTION 'Target-ahead version test failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=111
     AND account_id='A6' AND has_latest_conflict
     AND has_null_amount AND amount_mismatch IS NULL
 ) THEN RAISE EXCEPTION 'Latest-version conflict/null ambiguity test failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=112
     AND account_id='A7' AND has_historical_conflict
     AND NOT has_latest_conflict AND amount_mismatch IS FALSE
 ) THEN RAISE EXCEPTION 'Historical conflict must remain a separate DQ flag'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.reconciliation_report WHERE trade_id=113
     AND account_id='A7' AND source_count=2 AND target_count=1
     AND NOT source_duplicate AND NOT is_missing
     AND amount_mismatch IS FALSE
 ) THEN RAISE EXCEPTION 'Different versions must not mean duplicate or missing'; END IF;

 IF (SELECT COUNT(*) FROM lab04.sla_event_report
     WHERE delivery_status='IN_FLIGHT') <> 3 THEN
   RAISE EXCEPTION 'In-flight cohort was misclassified';
 END IF;
 IF (SELECT COUNT(*) FROM lab04.sla_event_report
     WHERE delivery_status='INVALID_TIMESTAMP') <> 1 THEN
   RAISE EXCEPTION 'Invalid SLA timestamp must be separately observable';
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.sla_summary WHERE cohort_label='pass_95'
     AND eligible_events=20 AND on_time_events=19 AND late_events=1
     AND overdue_undelivered_events=0 AND on_time_percent=95.00 AND sla_met
 ) THEN RAISE EXCEPTION '95 percent SLA passing cohort failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.sla_summary WHERE cohort_label='fail_90'
     AND eligible_events=20 AND on_time_events=18 AND late_events=1
     AND overdue_undelivered_events=1 AND on_time_percent=90.00 AND NOT sla_met
 ) THEN RAISE EXCEPTION '90 percent SLA failing cohort failed'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM lab04.sla_event_report WHERE event_id=1001
     AND receipt_count=2 AND delivery_status='ON_TIME'
 ) THEN RAISE EXCEPTION 'Retried delivery inflated SLA event count'; END IF;

 RAISE NOTICE 'Session 04 SQL assertions passed (fixture-based checks)';
END
$$;
