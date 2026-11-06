-- Session 02 / Task 1: initial candidate solution, preserved verbatim.
-- Status: UNDER REVIEW. No reference solution or fixes included.
-- Source: learner's live-coding answer (2026-11-06).
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
        FROM lab02.trade_versions)
SELECT trade_id,
       account_id,
       version,
       event_time,
       ingested_at,
       ingest_id,
       pnl,
       status
FROM trade_versions_cte
WHERE r = 1;
