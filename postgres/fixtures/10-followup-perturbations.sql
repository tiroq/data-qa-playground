-- Session 10 follow-up ONLY, after original timed answers have been saved.
-- Idempotent under primary keys. Adds records ONLY in isolated lab10.
-- WARNING: run AFTER baseline lab10 smoke (which expects exactly 12+12 rows).
-- The file is intentionally not loaded by Compose or CI.
INSERT INTO lab10.source_events
 (src_id,trade_id,account_id,version,event_id,created_at,pnl,status)
VALUES
 (13,304,'A2',2,'S304-CONFLICT','2026-11-08 12:04:30+00',4.2500,'FILLED'),
 (14,311,'A6',1,'S311-1','2026-11-08 12:11:00+00',NULL,'FILLED')
ON CONFLICT (src_id) DO NOTHING;

INSERT INTO lab10.target_events
 (target_id,trade_id,account_id,version,event_id,available_at,pnl,status)
VALUES
 (113,311,'A6',1,'S311-1','2026-11-08 12:12:00+00',NULL,'FILLED')
ON CONFLICT (target_id) DO NOTHING;
