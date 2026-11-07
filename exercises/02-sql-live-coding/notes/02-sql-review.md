# Session 02 — SQL Live Coding — Review Notes

**Date:** 2026-11-06 (Asia/Bangkok)  
**Status:** Learning interview completed across Tasks 1–3; runtime verification pending.  
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

### Mentor walkthrough (requested by candidate)

Candidate explicitly stopped the live-coding follow-up and asked for a full explanation. The reference was then added as [02-account-pnl-reviewed.sql](../solutions/02-account-pnl-reviewed.sql). **This is mentor-authored, not candidate-authored and not proof of candidate mastery.** The original attempt and provisional score (6/10) remain unchanged.

Core sequence:
1. Compute MAX(version) per trade/account.
2. Keep **all** rows matching that maximum.
3. Deduplicate relevant payload fields with `DISTINCT (trade_id, account_id, event_time, status, pnl)` and mark `COUNT(*) > 1` as a same-version conflict.
4. Independently rank trades deterministically; join the trade-level conflict before aggregating.
5. Count FILLED only for latest rows, SUM their PnL and `BOOL_OR` DQ flags at the account grain.
6. In this conservative policy, return NULL total_pnl if any same-version conflict is present or the selected FILLED trade has missing PnL. `has_conflict` only describes a payload conflict; missing PnL is a **separate** DQ issue.

Fixture-derived expected output: A1: 2, 5.5000, false; A2: 1, 9.0000, false; A3: 1, NULL, true.

Open contract question: What exact fields form a version payload? Here we assume event_time, status and pnl. Version-tied contradictory statuses would also make representative filled counts potentially untrusted. The reference uses conservative fail-closed reporting.

### Verification status

Reference has **not** been executed against PostgreSQL; outputs are derived from the checked-in fixture. Final session review and independent candidate mastery remain pending.


## Task 3 — PostgreSQL DISTINCT ON candidate attempt

**Attempt:** [03-distinct-on-attempt.sql](../solutions/03-distinct-on-attempt.sql)
**Status:** SQL component reviewed; conceptual comparison and ClickHouse argMax follow-ups pending.
**Provisional SQL score:** 9.5/10 (static review, not executed).

The candidate used `SELECT DISTINCT ON (trade_id, account_id)` and `ORDER BY trade_id, account_id, version DESC, event_time DESC, ingest_id DESC`. This is a valid PostgreSQL pattern for choosing one deterministically ranked physical row per logical key, including a unique `ingest_id` tie breaker. All eight requested columns are present. It is not a correctness proof for ambiguous same-version PnL (trade 205).

Minor contract mismatch: resulting display ordering is by `trade_id, account_id`, whereas original Task 1 required `account_id, trade_id`; a wrapper query would be needed to sort output separately while satisfying DISTINCT ON prefix restrictions. The original submission includes a harmless commented-out `WHERE rn = 1`.

**Follow-ups pending:** articulate the semantic/portability differences between `ROW_NUMBER()` and `DISTINCT ON`, the behavior of omitted ORDER BY, and ClickHouse `argMax` tie/payload consistency. No reference comparison has been presented yet.


### Candidate conceptual follow-up — DISTINCT ON vs ROW_NUMBER

**Candidate's explanation (summarized, not verbatim):** DISTINCT ON groups/deduplicates and takes a representative row using ORDER BY; ROW_NUMBER was thought to support more complex selection logic; without ORDER BY, DISTINCT ON makes no guaranteed choice of physical row.

**Review:** 8/10 for the conceptual comparison; correct core distinctions and exact response for missing ORDER BY (10/10). Correction: both support complex ORDER BY expressions, including CASE and multiple tie breakers. ROW_NUMBER is more flexible for top-N per group and exposes ranks; DISTINCT ON is PostgreSQL-specific and returns just one representative row per key. Both require authoritative domain rules to choose latest state; maximum PnL alone is not synonymous with latest version.

**Status:** PostgreSQL comparison reviewed. ClickHouse argMax follow-up subsequently completed; see below. Scores are component-only.


## Task 3 — ClickHouse argMax candidate conceptual response

**Conceptual score:** 9/10.

The candidate correctly described `argMax(pnl, version)` as the `pnl` value corresponding to the highest version, contrasted it with `MAX(pnl)`, expressed uncertainty (correctly) about equal-version ties, and correctly identified that separate argMax aggregates over `pnl` and `status` need not choose values from the same physical row.

Corrections: `MAX` returns the greatest aggregate value, not "all" values. Equal-maximum ties are **nondeterministic**, not guaranteed first; independent nullable args can be taken from different versions because `argMax` skips NULLs. A tuple argument keeps the chosen payload together; a lexicographic tuple comparison key `(version, event_time, ingest_id)` gives a deterministic representative if ingest_id is unique; no selection rule by itself validates the disputed PnL in trade 205.

**Official source:** https://clickhouse.com/docs/reference/functions/aggregate-functions/argMax  
**Saved full comparison:** [03-sql-alternatives.md](03-sql-alternatives.md).

## Session 02 — overall debrief

**Overall qualitative assessment: 7.5/10.** This is a learning assessment based on candidate attempts and discussion, **not** a verified execution score. Performance summary: Task 1 7.5/10, Task 2 6/10 (mentor walkthrough requested), Task 3 DISTINCT ON SQL 9.5/10 / comparison theory 8/10 / argMax 9/10.

**Three priority areas for next practice:**
1. Ranking semantics: window `ORDER BY` determines `ROW_NUMBER`; a query-level `ORDER BY` cannot change the rank.
2. Data quality: inspect all candidate rows of the highest business version and compare business payloads **before** deduplication; keep NULL/missing-value indicators distinct from conflicting-value indicators and block untrusted aggregates.
3. ClickHouse: `argMax` equal-version nondeterminism, independent column selection, tuple payload/tuple tie-break keys, and NULL-skipping behavior.

**Unverified items:** No runtime has executed these SQL submissions or mentor reference queries. The results reported in these notes are fixture-derived predictions, not observed outputs; CI is not claimed to pass. The PostgreSQL fixture check and SQL verification remain a completion gate. ROADMAP remains IN PROGRESS for this reason.

**No invented achievements:** The reviewed solutions and code samples written by the mentor are explicitly labeled reference material, not counted as unaided candidate solutions.
