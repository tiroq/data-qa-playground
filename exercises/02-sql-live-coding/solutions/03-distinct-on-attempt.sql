-- Session 02 / Task 3 / PostgreSQL DISTINCT ON
-- Candidate's original submission; preserved without SQL corrections.
-- Static review: syntactically correct PostgreSQL approach, deterministic
-- tie breaker with ingest_id. Final presentation order differs from task 1.
SELECT DISTINCT ON (trade_id, account_id)
    trade_id,
    account_id,
    version,
    event_time,
    ingested_at,
    ingest_id,
    pnl,
    status
FROM lab02.trade_versions
-- WHERE rn = 1
ORDER BY trade_id, account_id, version DESC, event_time DESC, ingest_id DESC;
