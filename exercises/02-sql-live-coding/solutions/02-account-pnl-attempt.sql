-- Session 02 / Task 2 — candidate's first live-coding submission.
-- Preserved verbatim; under review, not a verified or reference solution.
WITH ranked AS (
    SELECT
        trade_id,
        account_id,
        version,
        event_time,
        ingested_at,
        ingest_id,
        pnl,
        status,
        ROW_NUMBER() OVER (
            PARTITION BY trade_id, account_id
            ORDER BY version DESC, event_time DESC, ingest_id DESC
        ) AS rn
    FROM lab02.trade_versions
)
SELECT
    account_id,
    count(*) AS filled_trade_count,
    sum(pnl) AS total_pnl,
    CASE WHEN pnl IS NULL THEN TRUE ELSE FALSE END AS has_conflict
    -- ,
    -- BOOL_OR(has_conflict) AS has_conflict


FROM ranked
WHERE rn = 1 AND status = 'FILLED'
GROUP BY account_id, has_conflict
ORDER BY account_id;
-- FROM ranked
-- WHERE rn = 1
-- ORDER BY account_id, trade_id;
