-- Structural seed checks only: do not test the interview's latest-PnL answer.
-- throwIf fails the client command on any count/cardinality mismatch.
SELECT throwIf(
    count() != 6
    OR uniqExact(ingest_id) != 6
    OR uniqExact(tuple(account_id, trade_id)) != 3,
    'lab03.trading_events: expected 6 physical rows, 6 ingest IDs and 3 logical keys'
) FROM lab03.trading_events;

SELECT throwIf(
    count() != 12
    OR uniqExact(ingest_id) != 12
    OR uniqExact(tuple(account_id, trade_id)) != 6,
    'lab03.trade_versions: expected 12 physical rows, 12 ingest IDs and 6 logical keys'
) FROM lab03.trade_versions;

SELECT
    'lab03.trading_events' AS dataset,
    count() AS physical_rows,
    uniqExact(tuple(account_id, trade_id)) AS business_keys
FROM lab03.trading_events;

SELECT
    'lab03.trade_versions' AS dataset,
    count() AS physical_rows,
    uniqExact(tuple(account_id, trade_id)) AS business_keys
FROM lab03.trade_versions;
