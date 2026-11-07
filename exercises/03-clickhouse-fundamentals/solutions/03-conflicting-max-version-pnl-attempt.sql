-- Session 03 candidate solution; original query preserved.
-- Review and NULL caveat: ../notes/03-clickhouse-review.md
-- Not runtime-verified.
WITH t AS (
    SELECT
        account_id,
        trade_id,
        max(version) AS max_version
    FROM lab03.trade_versions
    GROUP BY account_id, trade_id
)
SELECT
    v.account_id,
    v.trade_id,
    groupArray(tuple(v.version, v.pnl, v.status)) AS states
FROM lab03.trade_versions AS v
INNER JOIN t
    ON v.account_id = t.account_id
    AND v.trade_id = t.trade_id
    AND v.version = t.max_version
GROUP BY
    v.account_id,
    v.trade_id
HAVING uniqExact(v.pnl) > 1
ORDER BY
    v.account_id,
    v.trade_id
