-- Session 02 / Task 1: reviewed REFERENCE approach, produced AFTER learner follow-up.
-- This deterministically selects one representative stored row per business trade,
-- NOT proof that a same-version conflicting payload is business-correct.
-- Assumption: business version is authoritative. event_time is secondary only
-- when its source semantics are trusted. ingest_id is a unique stable last tie-breaker.
-- Report same-version, conflicting-payload rows separately as a data-quality violation.
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
    trade_id,
    account_id,
    version,
    event_time,
    ingested_at,
    ingest_id,
    pnl,
    status
FROM ranked
WHERE rn = 1
ORDER BY account_id, trade_id;

-- Important: trade 205 has two rows of version 2 with matching event_time
-- but unequal pnl. The unique ingest_id makes the selection repeatable,
-- but does not validate whether pnl=8.5000 or pnl=8.0000 is correct.
-- Do NOT publish unverified account-level PnL from this output.
