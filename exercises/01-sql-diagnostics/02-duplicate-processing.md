# Exercise 2 — Duplicate Processing: Query and Design Rationale

## Objective and business contract

Find composite business keys with multiple processing rows. The initial exercise contract assumes **exactly one** processing row per `(trade_id, account_id)`. Real trading pipelines can support multiple legitimate attempts or lifecycle events; in such systems, redefine the uniqueness rule using `event_id`, attempt, version, and event type *before* labeling rows defective.

## Reference SQL

```sql
SELECT
    p.trade_id,
    p.account_id,
    COUNT(*) AS processing_count
FROM processed_trades AS p
GROUP BY p.trade_id, p.account_id
HAVING COUNT(*) > 1
ORDER BY processing_count DESC, p.trade_id, p.account_id;
```

Expected initial result (the two rows tie on count; the secondary sort fixes their order):

| trade_id | account_id | processing_count |
|---|---|---:|
| 102 | A1 | 2 |
| 105 | A3 | 2 |

## Why each component matters

1. **Read `processed_trades` directly**: uniqueness is a property of records in that table, not of the intersection with source trades. An `INNER JOIN trades` hides duplicate processing keys that have no parent source record. Example: two `(999, A9)` processing rows must still be detected, even when the source trade is missing.
2. **Group by the *full* business key**: matching only `trade_id` may conflate accounts, particularly when trade IDs are scoped or corrupt. The lab's business identity explicitly includes `account_id`.
3. **Do not group by `status` or `record_id`**: two records for the same trade can carry `SUCCESS` and `FAILED`. Grouping by status splits the logical key into separate groups, hiding duplicates. Grouping by unique `record_id` makes every group size one.
4. **`COUNT(*)`** counts all physical processing rows, independently of their status or nullable fields. By contrast `COUNT(status)` ignores null statuses and may undercount. In this query, a grouped row is itself a real processing record, so `COUNT(*)` is appropriate.
5. **`HAVING COUNT(*) > 1`** filters *groups after aggregation*. `WHERE` filters individual rows before aggregation and cannot directly reference `COUNT(*)` at the same query level.
6. **Deterministic ordering**: sort by count descending for severity, then key for stable manual or automated comparison.

## Why identical payloads are not a sufficient definition

Two identical values can represent duplicate delivery of one Kafka event, or two intentionally distinct events with coincidentally identical business attributes. Conversely, two records with different statuses may be duplicate representations of one expected *final* state, or a legitimate transition. Establish:

- The grain of the dataset: one row per trade, processing attempt, or lifecycle event?
- The immutable event identifier and idempotency key, if available.
- Whether the target stores latest state, an append-only event log, or both.
- The accepted retry semantics and duplicate-delivery strategy.

For the **exercise**, multiple rows per composite key are always a violation. In production, enforce the *documented* grain, not this simplified assumption.

## NULL semantics and quality rules

PostgreSQL `GROUP BY` places `NULL` values in the same grouping bucket for matching remaining columns. Two `(NULL, A7)` rows are counted as a repeated group, but this does **not** establish that they represent the same trade. Treat missing required identifiers as an independent `NULL_KEY` violation.

An optional companion DQ query:

```sql
SELECT record_id, trade_id, account_id, status
FROM processed_trades
WHERE trade_id IS NULL OR account_id IS NULL
ORDER BY record_id;
```

For recurring ingestion, deduplicate with stable event identifiers and persistent state or idempotent writes. Batch-local `DISTINCT` alone cannot prevent the same event reappearing in a later batch.

## Verification scenarios

1. Initial seed: keys `(102, A1)` and `(105, A3)`, each with count 2.
2. Two target-only rows `(999, A9)`: a third duplicate group appears even though no source row exists.
3. Same key, different statuses: group still counts both records.
4. Same key, one null status: `COUNT(*)` still counts the row.
5. Two rows with `trade_id = NULL`: PostgreSQL groups them, but separately flag them as invalid key data.

**Takeaway:** duplicate detection is a **uniqueness check at a clearly defined record grain**. Start with the target table; do not let a join or a status field accidentally erase evidence.
