WITH processing_count_cte AS
    (SELECT t.trade_id as t_trade_id,
            processed.trade_id as p_trade_id,
            t.account_id,
            processed.status as p_status,
            count(*) as processing_count
     from trades as t
     FULL JOIN processed_trades as processed ON t.trade_id = processed.trade_id
     AND processed.account_id = t.account_id -- WHERE processed.trade_id IS NULL
GROUP BY t.trade_id,
         processed.trade_id,
         processed.status,
         t.account_id)
SELECT t_trade_id,
       account_id,
       CASE
           WHEN t_trade_id IS NULL THEN 'ORPHAN'
           WHEN p_trade_id IS NULL THEN 'MISSING'
           WHEN processing_count > 1 THEN 'DUPLICATE'
           WHEN p_status = 'FAILED' THEN 'FAILED'
           WHEN p_status IS NULL THEN 'UNKNOWN'
           ELSE 'OK'
       END AS dq_status
FROM processing_count_cte;