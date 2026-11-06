# Session 02 — SQL Live Coding — Review Notes

**Date:** 2026-11-06 (Asia/Bangkok)  
**Status:** IN PROGRESS — Task 1 reviewed; Task 2 initial attempt under follow-up; Task 3 pending.  
**Attempts:** [initial SQL](../solutions/02-latest-trades.sql), [candidate follow-up SQL](../solutions/02-latest-trades-followup.sql), [reviewed reference approach](../solutions/02-latest-trades-reviewed.sql)  
**Provisional Task 1 score after follow-up:** 7.5/10 (static review only). This is **not** the final session score.

## Task 1 — Latest trade state per logical key

**Physical grain:** one ingestion/storage record per `ingest_id` in `lab02.trade_versions`.  
**Logical grain:** one trade state per `(trade_id, account_id)`.  
**Candidate answer:** `ROW_NUMBER() OVER (PARTITION BY trade_id, account_id ORDER BY version DESC)`, filtered to `r = 1`; selects all eight requested columns.

### Static review — strengths

- Correct composite logical key; no split by `status`.
- Prioritizes business `version` over ingestion order, avoiding the late-arrival trap for trade 203.
- Produces at most one stored row per logical key (where the input key exists).
- Preserves rows with `NULL` `pnl` or `status`; no accidental filter.
- All eight required output fields are present, including `ingest_id`.

### Open issues / edge cases

1. **High — nondeterministic version ties.** `ORDER BY version DESC` does not define which row wins among equal versions (trade 201: ingest 2/3; trade 205: ingest 10/11).
2. **High — unresolved conflicting values.** Trade 205 has identical top version and event time but different PnL (8.0000 vs 8.5000); choosing a row deterministically does not establish business correctness. A reconciliation / DQ policy must flag or quarantine the conflict independently of a display choice.
3. **Medium — no final stable order.** Task requires `ORDER BY account_id, trade_id` for results; window ordering alone does not guarantee output order.
4. **Unstated contracts.** Candidate did not explicitly describe physical and logical grain, handling of ties, or whether ingestion order is authoritative. This does not invalidate the query shape, but leaves acceptance criteria incomplete.

### Follow-up — candidate responded

- Added `ORDER BY account_id, trade_id` to the outer query: **correct** and now guarantees display ordering.
- Added `ORDER BY version, event_time DESC` to the CTE query **outside** the `ROW_NUMBER() OVER (...)` expression: **does not change rank assignments**. Ranking still depends only on `version DESC`; version ties remain unresolved. Furthermore, `version` ascending in that CTE sort does not match the intended business order.
- Business reasoning: candidate distinguished `ingested_at` from `event_time`; correctly rejected ingestion order as authoritative; suggested comparing business payload fields, separating retries from out-of-order delivery, and escalating same-version conflicts for investigation.
- Remaining nuance: for trade 205 the conflicting version-2 rows share **exactly the same event_time**, so event-time ordering cannot resolve the contradiction. `event_time` itself is trusted only if the source defines that semantic.
- Corrected reference query stored separately after follow-up, ranking by `version DESC, event_time DESC, ingest_id DESC` and sorting final output by `account_id, trade_id`. Unique `ingest_id` breaks residual ties deterministically; this is a **representative** row selection, not validation of the data.
- Data-quality policy: report identical deliveries separately from conflicting payloads for the same logical key/version; do not silently publish a potentially incorrect financial aggregate from unresolved conflicts.
- **Score rationale:** 7.5/10 for Task 1 after follow-up — correct window partitioning, selected columns, NULL preservation, version precedence, final ordering, and sound DQ reasoning; one critical unfixed SQL tie-break bug. Business reasoning alone approximates 9/10.

### Next work

- Complete account-level latest PnL with deduplication before aggregation.
- Compare `DISTINCT ON` / `ROW_NUMBER()` / ClickHouse `argMax`, including tie semantics.
- Execute SQL on PostgreSQL and capture observed results; the reference is not a substitute for a live test.

### Verification evidence

- **Static review only.** No live PostgreSQL query, `docker compose` run, or result-row assertion has been performed in this review.
- Fixture expectations from checked-in SQL: 12 physical rows, 6 logical keys.
- Reviewed reference approach is recorded, but **not executed**; final session score and edge-case test evidence remain pending.


## Task 2 — Account-level latest PnL: initial attempt

**Candidate:** [02-account-pnl-attempt.sql](../solutions/02-account-pnl-attempt.sql)  
**Preliminary score:** 6/10, static review; subject to follow-up and actual execution. The query has **not** been executed in a live PostgreSQL instance.

### What works

- Uses `ROW_NUMBER()` with the correct composite trade key, business-version priority and unique last tie-breaker.
- Filters on `rn = 1` **before** `status = 'FILLED'`: this avoids including historic filled versions of trades now cancelled.
- Aggregates using `COUNT(*)`, `SUM(pnl)` and `GROUP BY` after latest-state selection, avoiding retry-driven duplication.
- Sorts final output by account and retains numeric precision for non-NULL values.

### Blocking bugs

1. **Critical:** `CASE WHEN pnl IS NULL THEN TRUE ELSE FALSE END AS has_conflict` is a missing-value indicator, not a same-version payload-conflict detector. It observes only the single ranked row that survived `rn = 1`; all other candidate rows are already discarded.
2. **High:** `GROUP BY account_id, has_conflict` changes the intended output grain from one row per account to up to two rows per account. PostgreSQL allows the selected expression alias as a grouping key here, but that is logically incorrect.
3. **High:** `SUM(pnl)` skips NULL values; its output may look valid despite missing values. Also a conflicting latest PnL must not be silently published.
4. **Critical:** Trade 205 has conflicting version-2 payload values (8.0000 and 8.5000) at identical `event_time`. The chosen ingest 11 value 8.5000 is deterministic but untrusted, so account A3 must have `has_conflict = true` and `total_pnl = NULL` under the task contract.

### Fixture-derived predictions (not observed execution)

- Candidate: A1 = 2 filled / 5.5000 / false, A2 = 1 / 9.0000 / false, A3 = 1 / 8.5000 / false.
- Required for A3: 1 filled / NULL / true; A1/A2 expected to remain unchanged.
- Trade 204 has NULL status and NULL PnL, but is not FILLED. Missing value and conflicting values are distinct DQ categories.

### Follow-up pending

- Detect latest-version ties with distinct payloads **before collapsing them** to one representative trade row.
- Reduce trade-level findings to one account-level `has_conflict` flag; do not add it as a grouping dimension.
- Ensure `total_pnl` is NULL for conflicting accounts.
- Explain behavior for a FILLED trade with NULL PnL and for an account with zero FILLED trades.

No reference solution added yet; maintain interview conditions until candidate follow-up.
