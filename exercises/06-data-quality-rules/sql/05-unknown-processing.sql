-- DQ-19: NULL or unsupported processing status.
-- This legacy Postgres processed-trades fixture uses SUCCESS / FAILED,
-- unlike the event-level NEW / FILLED / CANCELLED / FAILED statuses.
SELECT p.record_id, p.trade_id, p.account_id, p.status
FROM processed_trades AS p
WHERE p.status IS NULL OR p.status NOT IN ('SUCCESS', 'FAILED')
ORDER BY p.trade_id, p.account_id, p.record_id;
