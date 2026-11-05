SELECT
    trade_id,
    account_id,
    COUNT(*) AS processing_count
FROM processed_trades
GROUP BY trade_id, account_id
HAVING COUNT(*) > 1
ORDER BY processing_count DESC;