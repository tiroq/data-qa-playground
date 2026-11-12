-- Read-only queries for an optional interview discussion.
-- Run after seeding a unique run_id; there is no merge-based deduplication here.
SELECT run_id, count() AS physical_rows, uniqExact(event_id) AS distinct_events,
       uniqExact(tuple(account_id, trade_id)) AS distinct_trades
FROM labstream.raw_events GROUP BY run_id ORDER BY run_id;

-- This is only a *candidate* latest-state projection and is NOT a defensible
-- financial aggregate if two equal maximum versions have different payloads.
SELECT run_id, account_id, trade_id,
       max(version) AS latest_version,
       argMax(tuple(pnl, status), tuple(version, event_time_ms, event_id)) AS candidate_state
FROM labstream.raw_events
GROUP BY run_id, account_id, trade_id
ORDER BY run_id, account_id, trade_id;
