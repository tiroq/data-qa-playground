# Exercise 3 — Full Reconciliation: Query and Design Rationale

## Objective

Reconcile source `trades` with target `processed_trades` and produce **one row per valid composite key**, showing the processing count, independent quality flags, and a single prioritized `dq_status`. Preserve source-only and target-only keys.

This is a snapshot-based lab. Production reconciliation additionally needs a completeness watermark, event-time rules, and an explicitly versioned business contract.

## Reference SQL — current schema (source keys are non-null)

```sql
WITH reconciliation AS (
    SELECT
        COALESCE(t.trade_id, p.trade_id) AS trade_id,
        COALESCE(t.account_id, p.account_id) AS account_id,
        BOOL_OR(t.trade_id IS NOT NULL) AS source_exists,
        COUNT(p.record_id) AS processing_count,
        COALESCE(
            BOOL_OR(p.record_id IS NOT NULL AND p.status = 'FAILED'),
            FALSE
        ) AS has_failed,
        BOOL_OR(
            p.record_id IS NOT NULL AND p.status IS NULL
        ) AS has_unknown
    FROM trades AS t
    FULL JOIN processed_trades AS p
        ON p.trade_id = t.trade_id
       AND p.account_id = t.account_id
    GROUP BY
        COALESCE(t.trade_id, p.trade_id),
        COALESCE(t.account_id, p.account_id)
)
SELECT
    trade_id,
    account_id,
    processing_count,
    has_failed,
    has_unknown,
    CASE
        WHEN NOT source_exists THEN 'ORPHAN'
        WHEN processing_count = 0 THEN 'MISSING'
        WHEN processing_count > 1 THEN 'DUPLICATE'
        WHEN has_failed THEN 'FAILED'
        WHEN has_unknown THEN 'UNKNOWN'
        ELSE 'OK'
    END AS dq_status
FROM reconciliation
ORDER BY trade_id, account_id;
```

The query assumes source keys are always present (enforced by `trades.trade_id PRIMARY KEY` and `trades.account_id NOT NULL`). The processing table intentionally allows nullable business fields. Invalid keys should receive a separate `NULL_KEY` classification rather than being trusted as valid business identities; see the caveat below.

## Expected result on the original seed

| trade_id | account_id | processing_count | has_failed | has_unknown | dq_status |
|---|---|---:|---|---|---|
| 101 | A1 | 1 | false | false | OK |
| 102 | A1 | 2 | false | false | DUPLICATE |
| 103 | A2 | 1 | true | false | FAILED |
| 104 | A2 | 1 | false | false | OK |
| 105 | A3 | 2 | false | false | DUPLICATE |
| 106 | A3 | 0 | false | false | MISSING |
| 107 | A4 | 1 | false | false | OK |
| 108 | A4 | 1 | false | true | UNKNOWN |
| 109 | A5 | 1 | false | false | ORPHAN |

## Why the query is structured this way

### 1. `FULL JOIN`: completeness in both directions

An `INNER JOIN` discards both source-only and target-only records. `LEFT JOIN` preserves source-only records but loses orphan target records. `FULL JOIN` retains **both**, allowing the report to distinguish:

- `MISSING`: source exists, no matching target record;
- `ORPHAN`: target exists, no matching source trade.

The `ON` clause uses both `trade_id` and `account_id` to enforce the documented matching identity. A target record with the correct trade ID but wrong account must not be reported as a successful match.

### 2. `COALESCE`: preserve identifiers on unmatched sides

`t.trade_id` and `t.account_id` become null for target-only rows, while target fields become null for source-only rows. `COALESCE` selects the known identifier from whichever side exists. Without it, orphan entries appear as blank keys despite having identifiers in `processed_trades`.

### 3. Group at the reconciliation grain — not the status grain

We need one row for each composite key, not one per status or physical record. Grouping by `p.status` creates separate groups for `SUCCESS` and `FAILED` for the same trade, so aggregate counts underreport duplicates. Grouping by `p.record_id` likewise fragments each processing record.

The selected `GROUP BY COALESCE(...)` is appropriate for this **initial valid-key dataset**; see the NULL-key qualification below. The query's output grain should be stated explicitly in tests.

### 4. `COUNT(p.record_id)` vs `COUNT(*)`

`FULL JOIN` creates a source-only row even when no processing row exists. Consequently, `COUNT(*)` would return **1** for a missing trade. `COUNT(p.record_id)` correctly returns **0**, because `record_id` is non-null for a real target row and null for the synthetic unmatched side.

This is a critical distinction between counting joined rows and counting actual processing records.

### 5. Use presence indicators, not business statuses, to decide existence

`source_exists` is derived from a guaranteed non-null source primary key. A missing source is `ORPHAN`; a present source with zero target records is `MISSING`. `status = 'FAILED'` and `status IS NULL` are qualities of an **existing target record**, not proof of its absence.

### 6. Aggregate status flags independently

`BOOL_OR(...)` answers whether *any* processing row satisfies a condition. This permits status classification without grouping by the raw `status`.

- `has_failed`: at least one *real* target record has `FAILED`.
- `has_unknown`: at least one *real* target record has `status IS NULL`.

The `p.record_id IS NOT NULL` guard is essential for `has_unknown`: on a source-only outer-join row, `p.status IS NULL` is true **even though no target processing record exists**. Without the guard, a missing trade is incorrectly marked as having an unknown processing status.

`COALESCE(BOOL_OR(...), FALSE)` converts an all-null boolean aggregate to a deterministic false value. The guarded `has_unknown` expression already produces a non-null boolean for joined rows.

### 7. Status priority: a single headline, not the complete truth

The lab specifies:

`ORPHAN > MISSING > DUPLICATE > FAILED > UNKNOWN > OK`

A key with two processing rows, including a failed row, gets headline `DUPLICATE`, but `has_failed = true` preserves the secondary fact. This avoids silently losing actionable information. In production, store multiple independent DQ flags and calculate a derived severity separately; priorities are policy decisions, not inherent SQL behavior.

### 8. Deterministic output and testability

`ORDER BY trade_id, account_id` makes sample outputs reproducible. Use automated checks for output cardinality, zero counts on missing trades, correct orphan identifiers, and status precedence. Do not assume that order is guaranteed without an explicit `ORDER BY`.

## NULL business keys: important limitation and safer production policy

The reference query follows the original exercise but is **not sufficient for a production data-quality report when business keys may contain NULLs**:

- `p.trade_id = t.trade_id` does not match null to null, because `NULL = NULL` evaluates to unknown.
- `GROUP BY` buckets null values together. Two distinct processing records `(NULL, A7)` may end up as one result with `processing_count = 2`, although neither can be proven to belong to the same trade.
- `IS NOT DISTINCT FROM` can match two null values, but doing so may create a **false positive business match**. Null-safe syntax is not a substitute for a business contract.
- If both sides of an outer join have nullable or incomplete keys, `COALESCE` can obscure the provenance of invalid rows.

**Recommended policy:** isolate invalid keys first; do not automatically match them as valid trades.

```sql
-- Invalid target business identities: investigate/quarantine separately.
SELECT record_id, trade_id, account_id, status
FROM processed_trades
WHERE trade_id IS NULL OR account_id IS NULL
ORDER BY record_id;
```

Reconcile only target rows with complete business keys, while retaining invalid rows in a separate `NULL_KEY` anomaly report (ideally per `record_id`). If a `NULL_KEY` row also has an orphan-like symptom, retain both facts but never present it as a trusted match.

## Verification cases

1. **Initial dataset**: nine business keys; 106 missing, 109 orphan, 102 and 105 duplicated, 103 failed, 108 unknown.
2. **Different statuses for same key**: add a `FAILED` record for 102; its count increases, `has_failed = true`, and headline remains `DUPLICATE`.
3. **Wrong account**: add `(106, A999)` in processing; original `(106, A3)` remains missing, and `(106, A999)` is orphan.
4. **Null status**: a real record with unknown status must be `UNKNOWN`, not `MISSING`.
5. **Absent processing**: count must be zero and `has_unknown = false`.
6. **Null business keys**: collect `NULL_KEY` records separately; do not treat null-equality as proof of matching.
7. **Multiple anomalies**: ensure the headline priority is respected without losing independent boolean flags.

## Production implications

- Define a stable **snapshot / watermark** before making missing-record assertions; Kafka lag and in-flight processing may otherwise cause false alarms.
- Separate **transport duplicates** from repeated business operations or legitimate state transitions.
- Prefer **event IDs or idempotency keys** for deduplication when an append-only event log is the target.
- Distinguish `FAILED` caused by a valid business rejection from an ETL parsing or infrastructure failure.
- Define **quarantine, retry, alerting, and quality gates** per anomaly severity, rather than stopping all ingestion for every malformed record.
- Test data volume and join cardinality; many-to-many joins can amplify counts when *both* sides contain duplicate business keys. Pre-aggregate by key on each side if source uniqueness cannot be trusted.

**Takeaway:** a reconciliation query is a compact implementation of a **business contract**: matching identity, expected cardinality, admissible states, anomaly precedence, and recovery policy. Every clause must support one of those rules.
