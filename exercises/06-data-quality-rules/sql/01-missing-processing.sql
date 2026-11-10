-- DQ-14 / BASELINE: Source trade without a matching processed business key.
-- Run only after the reconciliation cutoff; pending events are NOT missing.
-- PostgreSQL seed: postgres/init/01-schema.sql.
SELECT t.trade_id, t.account_id, 'MISSING' AS reason
FROM trades AS t
WHERE NOT EXISTS (
    SELECT 1 FROM processed_trades AS p
    WHERE p.trade_id = t.trade_id AND p.account_id = t.account_id
)
ORDER BY t.trade_id, t.account_id;
