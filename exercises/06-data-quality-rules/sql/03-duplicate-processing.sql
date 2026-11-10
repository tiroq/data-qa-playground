-- DQ-15 / BASELINE: Multiple processed snapshot rows for one composite key.
-- This is NOT DQ-02 event-id replay and is NOT valid for a versioned event log.
SELECT p.trade_id, p.account_id,
       COUNT(*) AS processing_count
FROM processed_trades AS p
WHERE p.trade_id IS NOT NULL AND p.account_id IS NOT NULL
GROUP BY p.trade_id, p.account_id
HAVING COUNT(*) > 1
ORDER BY processing_count DESC, p.trade_id, p.account_id;
