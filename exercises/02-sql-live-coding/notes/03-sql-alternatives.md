# Session 02 — SQL Alternatives: PostgreSQL vs ClickHouse

**Status:** Interview discussion completed; examples are explanatory and have not been executed in a local database.

## Candidate assessment

- PostgreSQL `DISTINCT ON` query: **9.5/10** (static SQL review). Correct composite identity and ordering `(trade_id, account_id, version DESC, event_time DESC, ingest_id DESC)`. Original Task 1 asked for display ordering `account_id, trade_id`, which needs an outer query.
- Conceptual comparison `ROW_NUMBER()` vs `DISTINCT ON`: **8/10**. Candidate correctly understood representative row selection and undefined selection without `ORDER BY`. Correction: complex `ORDER BY` rules are available to both; `ROW_NUMBER()` generalizes to top-N and annotating all rows, and is portable.
- ClickHouse `argMax` reasoning: **9/10**. Correctly explained that `argMax(pnl, version)` returns the PnL at the highest version, not the maximum PnL; expressed justified uncertainty about ties; correctly flagged the lack of a cross-column same-row guarantee for independent aggregates. Minor correction: `MAX(x)` returns one maximum aggregate, not all values.

## Essential semantics

`argMax(arg, val)` returns the `arg` associated with the maximum `val`. An exact tie in `val` is nondeterministic, and nullable arguments may be skipped. Independent `argMax(pnl, version)` and `argMax(status, version)` may come from different physical rows (or versions where individual arguments are NULL).

See: https://clickhouse.com/docs/reference/functions/aggregate-functions/argMax

## PostgreSQL DISTINCT ON attempt

Candidate code is preserved in [03-distinct-on-attempt.sql](../solutions/03-distinct-on-attempt.sql).

```sql
SELECT DISTINCT ON (trade_id, account_id)
    trade_id, account_id, version, event_time,
    ingested_at, ingest_id, pnl, status
FROM lab02.trade_versions
ORDER BY trade_id, account_id, version DESC,
         event_time DESC, ingest_id DESC;
```

The ORDER BY prefix must match the DISTINCT ON expressions. The `DISTINCT ON` query does not detect payload conflicts and must be supplemented with a DQ check.

## ClickHouse equivalent for consistent-row selection

Assumes a ClickHouse table with the corresponding columns and globally unique, stable `ingest_id` within each logical trade. This is a **reference design**, not candidate-authored SQL:

```sql
SELECT
    trade_id,
    account_id,
    argMax(
        tuple(pnl, status, version, event_time, ingested_at, ingest_id),
        tuple(version, event_time, ingest_id)
    ) AS selected_state
FROM trade_versions
GROUP BY trade_id, account_id
ORDER BY account_id, trade_id;
```

The first tuple keeps data from a *single stored row* and preserves nullable fields inside the tuple. The second tuple orders lexicographically: version first, then event_time, then unique ingest_id. It provides deterministic **representation**, not financial truth. If ingest_id is not unique, the final ordering may still tie.

Example contrast:

| version | pnl | `max(pnl)` | `argMax(pnl, version)` |
|---|---|---|---|
| 1 | 1.0000 | 1.0000 | — |
| 2 | 0.5000 | — | 0.5000 |

For trade 205, version 2 appears with pnl=8.0000 and pnl=8.5000 and the same event_time. Without a tie-breaker, either could be selected. Even a deterministic choice must be flagged as an unresolved same-version conflict before reporting aggregated PnL.

## Post-interview follow-up priorities

1. Distinguish window `ORDER BY` from query-level `ORDER BY`, and satisfy the required output grain and ordering.
2. Detect same-version payload conflicts *before* reducing rows to one per trade; keep conflict vs missing-value DQ flags separate.
3. Drill ClickHouse `argMax` tie resolution, tuple payloads, and NULL-skipping behavior; validate with actual ClickHouse during a later session.

**Execution:** PostgreSQL and ClickHouse examples were not actually run in this ChatGPT review.
