SELECT count(*) as processing_count,
    t.trade_id,
       t.account_id,
       t.symbol
FROM trades as t
JOIN processed_trades as processed ON t.trade_id = processed.trade_id
      AND processed.account_id = t.account_id
GROUP BY t.trade_id,
         t.account_id,
         t.symbol
HAVING COUNT(*) > 1
ORDER BY processing_count DESC;

-- WHERE processed.trade_id IS NULL;