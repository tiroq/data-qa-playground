-- DQ-14 / BASELINE: Target processing row without a source business key.
-- Invalid NULL keys are diagnosed separately rather than labeled orphan.
SELECT p.trade_id, p.account_id, p.record_id, 'ORPHAN' AS reason
FROM processed_trades AS p
WHERE p.trade_id IS NOT NULL AND p.account_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM trades AS t
      WHERE t.trade_id = p.trade_id AND t.account_id = p.account_id
  )
ORDER BY p.trade_id, p.account_id, p.record_id;
