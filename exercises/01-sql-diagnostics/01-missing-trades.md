# Exercise 1 — Missing Trades: Query and Design Rationale

## Objective and business contract

Detect a source trade that has **no corresponding processing record**. In this lab, a logical match requires both `trade_id` and `account_id` to match. A processing record with `FAILED` or a `NULL` status **exists**; it is not a missing record. We do not infer business success from mere existence.

Source: `trades` (one row per globally unique `trade_id`). Target: `processed_trades` (intentionally allows duplicate, orphan, and invalid processing rows).

## Reference SQL

```sql
SELECT
    t.trade_id,
    t.account_id,
    t.symbol
FROM trades AS t
LEFT JOIN processed_trades AS p
    ON p.trade_id = t.trade_id
   AND p.account_id = t.account_id
WHERE p.record_id IS NULL
ORDER BY t.trade_id;
```

Expected result on the initial seed:

| trade_id | account_id | symbol |
|---|---|---|
| 106 | A3 | GBPUSD |

## Why each component matters

1. **Start with `trades`**: we ask which *source* trades have no processing record. Starting from `processed_trades` instead would describe orphans, the reverse question.
2. **`LEFT JOIN` rather than `INNER JOIN`**: preserves source rows even when the target side has no match. An inner join silently discards exactly the missing rows we need to inspect.
3. **Composite join condition**: `trade_id` alone may be sufficient for globally unique source identifiers, but the DQ contract additionally requires a matching account. If `(106, A999)` appears in the target while the source has `(106, A3)`, a trade-id-only join incorrectly declares the source trade present.
4. **`WHERE p.record_id IS NULL`**: `record_id` is a non-null primary key. A null after the outer join therefore proves the target row was absent. Filtering on `p.status IS NULL` is **wrong**: a real processing row can legitimately have an unknown status. Checking a nullable business key may also be ambiguous. `record_id` is the reliable presence indicator.
5. **No `DISTINCT` or aggregation**: a source trade without matching target produces exactly one left-only row. Duplicate *matching* target rows disappear through the anti-join filter; they cannot multiply the missing-trade output.
6. **`ORDER BY`** makes verification deterministic; without ordering, SQL does not guarantee result order.

## Equivalent anti-join using NOT EXISTS

```sql
SELECT t.trade_id, t.account_id, t.symbol
FROM trades AS t
WHERE NOT EXISTS (
    SELECT 1
    FROM processed_trades AS p
    WHERE p.trade_id = t.trade_id
      AND p.account_id = t.account_id
)
ORDER BY t.trade_id;
```

`NOT EXISTS` expresses the absence test directly and avoids accidental row multiplication. Use either form according to readability and the execution plan; never assume one is always faster.

## Important edge cases

- **`FAILED` vs missing**: trade 103 has a processing row with `FAILED`, so it is *not* returned.
- **Unknown status vs missing**: trade 108 has a processing row with `status IS NULL`; it is *not* returned.
- **Duplicate processing**: trades 102 and 105 have two matching target records; neither is missing.
- **Orphan target**: `(109, A5)` is absent from source. This source-focused query does not report it. Use a separate orphan check or full reconciliation.
- **Partial keys**: with `=`, comparisons involving `NULL` evaluate to `UNKNOWN`, not true. A missing or nullable key should generally be reported as `NULL_KEY` rather than silently null-matched. The current source schema disallows nulls in its key.
- **Eventual consistency**: in an asynchronous ETL pipeline, no target row *yet* does not necessarily mean a lost trade. Compare only data past an agreed completeness watermark/window and define when to escalate.

## Verification scenarios

1. Initial seed: returns only `(106, A3)`.
2. Insert `(new record_id, 106, A999, 'SUCCESS')`: still returns `(106, A3)` because the account differs.
3. Insert `(new record_id, 106, A3, 'FAILED')`: 106 is no longer *missing*, though its business processing is failed.
4. Insert another target row for 102: missing-trade result does not change.

**Takeaway:** missing-record validation is an **existence check across a declared business identity**, not a test for successful processing.
