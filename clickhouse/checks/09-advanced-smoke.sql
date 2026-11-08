-- Raw fixture readiness only; does NOT verify learner's MV or aggregation.
SELECT throwIf(
    count() != 12 OR uniqExact(ingest_id) != 12
    OR uniqExact(tuple(trade_id, account_id)) != 6,
    'Session 09 fixture mismatch: expected 12 physical rows, unique ingest IDs, 6 keys'
) FROM lab09.raw_events;

SELECT 'lab09 fixture ready' AS message, count() AS physical_rows
FROM lab09.raw_events;
