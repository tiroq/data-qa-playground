-- Session 03 — Candidate's first syntactically valid account-PnL query.
-- Supplied in chat; execution output has not been provided/verified.
-- Relies on lab03.trading_events_latest being built with
-- ReplacingMergeTree(version), ORDER BY (account_id, trade_id),
-- and a stable partition key per logical trade.
SELECT account_id,
SUM(pnl) AS total_pnl
FROM trading_events_latest FINAL
GROUP BY account_id
ORDER BY account_id;
