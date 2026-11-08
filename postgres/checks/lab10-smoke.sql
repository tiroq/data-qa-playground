-- Fixture smoke only: does not check learner SQL mock solutions.
DO $$
BEGIN
 IF (SELECT COUNT(*) FROM lab10.source_events) <> 12 THEN
  RAISE EXCEPTION 'Expected 12 source physical rows';
 END IF;
 IF (SELECT COUNT(*) FROM lab10.target_events) <> 12 THEN
  RAISE EXCEPTION 'Expected 12 target physical rows';
 END IF;
 IF (SELECT COUNT(*) FROM lab10.source_events WHERE trade_id IS NULL OR account_id IS NULL) <> 1 THEN
  RAISE EXCEPTION 'Expected one source invalid key';
 END IF;
 IF (SELECT COUNT(*) FROM lab10.target_events WHERE trade_id IS NULL OR account_id IS NULL) <> 1 THEN
  RAISE EXCEPTION 'Expected one target invalid key';
 END IF;
END $$;
SELECT 'lab10 fixture ready' AS result;
