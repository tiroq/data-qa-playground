-- Session 02 / Task 1: candidate's second attempt (follow-up).
-- Preserved exactly as written by the learner. Not a reference solution.
-- Static review: final result ordering is fixed, but ROW_NUMBER ties remain unresolved.
WITH trade_versions_cte AS
       (SELECT ROW_NUMBER() OVER (PARTITION BY trade_id, account_id
                                  ORDER BY version DESC) AS r,
               trade_id,
               account_id,
               version,
               event_time,
               ingested_at,
               ingest_id,
               pnl,
               status
        FROM lab02.trade_versions
        ORDER BY version, event_time DESC
        )
SELECT trade_id,
       account_id,
       version,
       event_time,
       ingested_at,
       ingest_id,
       pnl,
       status
FROM trade_versions_cte
WHERE r = 1
ORDER BY account_id, trade_id;
