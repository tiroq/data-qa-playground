-- DQ-18: Explicit FAILED rows are present, not MISSING.
SELECT p.record_id, p.trade_id, p.account_id, p.status
FROM processed_trades AS p
WHERE p.status = 'FAILED'
ORDER BY p.trade_id, p.account_id, p.record_id;
