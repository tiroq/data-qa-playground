WITH processing_count_cte AS
    (SELECT COALESCE(t.trade_id, processed.trade_id) AS trade_id,
            COALESCE(t.account_id, processed.account_id) AS account_id,
            t.trade_id as t_trade_id,
            processed.trade_id as p_trade_id,
            COUNT(processed.record_id) as processing_count,
            COALESCE(BOOL_OR(processed.status = 'FAILED'), FALSE) AS has_failed,
            BOOL_OR(processed.record_id IS NOT NULL
                    AND processed.status IS NULL) AS has_unknown
     from trades as t
     FULL JOIN processed_trades as processed ON t.trade_id = processed.trade_id
     AND processed.account_id = t.account_id -- WHERE processed.trade_id IS NULL
GROUP BY t.trade_id,
         processed.trade_id,
         COALESCE(t.trade_id, processed.trade_id),
         COALESCE(t.account_id, processed.account_id),
         t.account_id)
SELECT trade_id,
       account_id,
       processing_count,
       CASE
           WHEN t_trade_id IS NULL THEN 'ORPHAN'
           WHEN p_trade_id IS NULL THEN 'MISSING'
           WHEN processing_count > 1 THEN 'DUPLICATE'
           WHEN has_failed THEN 'FAILED'
           WHEN has_unknown THEN 'UNKNOWN'
           ELSE 'OK'
       END AS dq_status
FROM processing_count_cte
ORDER BY trade_id;