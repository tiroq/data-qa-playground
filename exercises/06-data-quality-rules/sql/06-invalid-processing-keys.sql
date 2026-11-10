-- DQ-01 / DQ-16: Invalid target business identity is its own anomaly.
-- Do not auto-assign NULL identities to arbitrary source keys.
SELECT p.record_id, p.trade_id, p.account_id,
       'INVALID_BUSINESS_KEY' AS reason
FROM processed_trades AS p
WHERE p.trade_id IS NULL OR p.account_id IS NULL
   OR btrim(p.account_id) = ''
ORDER BY p.record_id;
