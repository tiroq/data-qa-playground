# Session 03 — ClickHouse Fundamentals: live review notes

**Date (Asia/Bangkok):** 2026-11-07  
**Session state:** IN PROGRESS — Part A discussed/reviewed; Part B and C not attempted yet.  
**Runtime evidence:** None recorded. Values below are hand-calculated expectations, not observed SQL output.

## Part A — Initial query diagnosis

**Candidate's reasoning (summarized, not a verbatim quote):** Grouping by `account_id` and summing `pnl` over every physical delivery incorrectly includes earlier versions and repeated deliveries. The result is not a defensible account-level latest-state PnL and varies with incoming deliveries.

**Candidate's numerical answer:**
- Original sum A1 = **22**, correct.
- Original sum A2 = **3**, incorrect (actual arithmetic: **3 + 1 = 4**).
- Expected latest-state sum A1 = **5** (trade T100 version 2 PnL 7, T101 PnL -2), correct.
- Expected latest-state sum A2 = **1** (T200 version 2), correct.
- Candidate explicitly raised uncertainty about repeated deliveries with the same version and the need to select one state.

**Mentor feedback:**
- The physical-row SUM is deterministic for a fixed snapshot; it is semantically incorrect, rather than mathematically random.
- The fixture assumes `pnl` is a total as-of-state value, not a delta event.
- Same-version identical payloads may represent exact replays; same-version contradictory payloads need an explicit business resolution or DQ rejection policy. A replacing engine alone does not establish which conflicting payload is authoritative.

**Provisional Part A score:** **2.5 / 3**, not a final session grade.

## Pending

- [ ] Part B: candidate-designed MergeTree / ReplacingMergeTree schema, partitioning, sorting and primary-key rationale.
- [ ] Part C: candidate SQL correctness across background merge states.
- [ ] Five follow-up questions and overall score /10.
- [ ] Execute ClickHouse fixture smoke checks, capture actual outputs and record verification.

## Part B — first oral attempt (without SQL)

**Candidate's initial reasoning (paraphrased):** Has not previously worked with `MergeTree`/`ReplacingMergeTree(version)`, suspects replacing by highest version is better for a current-state table, and explicitly worries about out-of-order delivery when versions are equal. Does not yet understand the respective roles of `ORDER BY` and `PARTITION BY`.

**Status:** Unassessed; no schema proposed yet. Tutor will explain the minimal semantics and ask the candidate to identify a logical sort/replacement key before writing any DDL. This is not a completed Part B solution.

## Part B — ORDER BY follow-up attempt

**Candidate selection:** `ORDER BY (account_id, trade_id, version)` for `ReplacingMergeTree(version)`.

**Review:** Incorrect replacement identity. Including `version` in the sorting key preserves different versions as distinct keys; similarly adding a unique `ingest_id` would prevent logical-state deduplication. Appropriate logical-state replacement identity under this exercise contract: `ORDER BY (account_id, trade_id)` (the `version` remains the engine argument). The candidate has not yet attempted `PARTITION BY`, `PRIMARY KEY`, full DDL, or query-time correctness.

**Important caveats from review:** asynchronous background merges mean ordinary `SELECT` cannot promise one row per logical key; ties on version with contradictory payload require DQ detection, not blind business acceptance. Background replacement is partition-scoped: choose partition fields stable across versions of a trade. No runtime result asserted.

## Part B — partition-boundary follow-up

**Question:** With `PARTITION BY toYYYYMM(event_time)`, trade T100 v1 (October) and v2 (November) share `ORDER BY (account_id, trade_id)`. Will background merges collapse them?

**Candidate answer (paraphrased):** The partition expression will split them into separate parts.

**Review:** Correct core intuition: versions land in different **partitions** (`202610`, `202611`), not merely different physical data parts. Background merges never cross the partition boundary, so both versions remain physically present. Tutor distinguishes ordinary background merge semantics from `SELECT ... FINAL` at query time and will ask the candidate to propose a stable partition strategy.

**Status:** Conceptual reasoning demonstrated; no local SQL runtime evidence and no user-authored DDL yet.

## Part B — stable partition key follow-up

**Question:** Given mutable `event_time` and immutable trade creation `trade_date`, propose `PARTITION BY` to keep all versions together.

**Candidate's answer (paraphrased):** Partition by `trade_date` at monthly granularity; the value is shared by every event for a logical trade, so all its versions remain in one partition.

**Review:** Correct. Concrete expression: `PARTITION BY toYYYYMM(trade_date)`, with an explicit data-quality invariant that `trade_date` is stable for every `(account_id, trade_id)`. Note: a `ReplacingMergeTree` current-state table cannot substitute for a retained append-only audit log.

**Status:** Candidate has selected the intended replacement key and partition key after guided corrections. Full user-authored DDL and independent query-time verification remain pending.

## Architecture discussion — one raw event table with a current-state abstraction

**Learner's question:** Can raw history remain in a plain `MergeTree` table while client applications read a latest-state view, without copying all events into a separate `ReplacingMergeTree` table?

**Mentor clarification (architectural explanation, NOT a learner-submitted solution):**
1. **Ordinary SQL `VIEW` on raw `MergeTree`:** no additional physical data, compute latest state using a business-key grouping and a version-aware aggregate such as `argMax(tuple(pnl, status), version)` at query time. This is a virtual abstraction, not a `ReplacingMergeTree` engine layered onto a source table; a raw `MergeTree` plus `FINAL` is not a replacement policy.
2. **Incremental materialized view + `AggregatingMergeTree`:** persist `argMaxState` per business identity and read via `argMaxMerge`; stores aggregate states instead of copying a full stream and shifts compute toward writes. Incremental MVs process inserted blocks, not source mutations/deletes or historical rows unless explicitly backfilled.
3. **Materialized view + `ReplacingMergeTree(version)`:** persist a second table of versioned rows if desired; for immediate query-time deduplication, queries must still use `FINAL`. This is a physical table, not a zero-copy wrapper.

**DQ caveats:** identical-version conflicting payloads cannot be resolved by maximum version alone; the authoritative ordering/tie policy must come from the data contract and conflicts may require quarantine. Preserve source event history for audit. Do not compute `sum(pnl)` directly over physical versions or incrementally sum new rows for a current-state PnL metric. Materialized-view backfill and recovery have to be tested against replay/late arrivals.

**Status:** Architecture question answered conceptually, no candidate-created DDL or observed execution recorded. Keep original hands-on Part B/Part C exercises pending.

## Lab SQL debugging — alias collides with aggregate input

**Observed by learner:** ClickHouse error `Aggregate function max(version) AS version is found inside another aggregate function in query` when running mentor's suggested latest-state VIEW query.

**Cause:** Mentor's original example used `max(version) AS version` alongside `argMax(tuple(pnl, status), version)`. ClickHouse can substitute a same-named SELECT alias into the other expression, effectively nesting `max(version)` inside `argMax`. **This was a mentor-provided query bug, not a candidate mistake.**

**Correction proposed (not yet locally rerun/verified):**

```sql
CREATE OR REPLACE VIEW lab03.v_latest_trades AS
SELECT
    account_id,
    trade_id,
    max(version) AS latest_version,
    argMax(tuple(pnl, status), version) AS state
FROM lab03.trading_events
GROUP BY account_id, trade_id;
```

**Caveat:** `argMax` does not guarantee a business-authoritative winner for contradictory payloads sharing the maximum version. The production data-quality contract must resolve or flag such conflicts before treating PnL as verified.

**Runtime status:** error text supplied by the learner; corrected query has not been independently executed or claimed passing.

## Part B — first candidate-authored CREATE TABLE

**Original attempt:** [solutions/03-trading-events-latest-attempt.sql](../solutions/03-trading-events-latest-attempt.sql). Exact learner-supplied DDL preserved, with only non-functional file comments. Not verified against a running database.

**Review:**
- **Correct:** relevant physical columns, logical replacement identity `ORDER BY (account_id, trade_id)`; `version` is not included in the replacement key.
- **Critical mistake:** `ENGINE = ReplacingMergeTree()` without a `version` parameter is not the same as choosing the highest business version. Under out-of-order deliveries, replacement may retain a stale state. Require explicit version-aware replacement.
- **Missing:** `PARTITION BY` with the already-discussed stable creation-date month. The omitted partition expression is syntactically legal, but does not meet the partition-design part of the exercise.
- **Source compatibility:** raw `lab03.trading_events.pnl` is `Nullable(Decimal(18,4))`, whereas the candidate used non-nullable `Decimal(18,4)`. The six-row Session 03 fixture has non-NULL PnL; however, the contract calls for NULL edge cases and a broader load could fail or need explicit filtering/default handling.
- **Future test:** check how `SELECT ... FINAL` behaves before background merges and why same-version conflicts require explicit data-quality rules.

**Provisional DDL review:** 1.5/3 on table-engine/key/partition design; not a complete session score. Ask learner to revise the DDL before showing a model answer. Note that if a table was already created locally, `CREATE TABLE IF NOT EXISTS` won't update its engine/schema: a new table name or an explicit drop/recreate (with data-loss warning) is needed.

## Part B — revised candidate-authored DDL

**Attempt:** [solutions/03-trading-events-latest-revised.sql](../solutions/03-trading-events-latest-revised.sql), saved from candidate's message without modifying the SQL. The copied introductory comment still calls it the 'original' attempt; the linked filename and this note distinguish it as the revision.

**Review:** The candidate corrected all the prior DDL deficiencies: uses `ReplacingMergeTree(version)`, `PARTITION BY toYYYYMM(trade_date)`, `ORDER BY (account_id, trade_id)`, and `Nullable(Decimal(18,4))` consistent with the raw table. **DDL design review 3/3 after feedback**; not evidence of independent first-pass proficiency.

**Operational caution:** `CREATE TABLE IF NOT EXISTS` will leave an already-created table unchanged. Inspect `SHOW CREATE TABLE lab03.trading_events_latest`; if a stale version exists, create a separately named table or explicitly drop/recreate only after checking its data.

**Pending runtime:** No observed ClickHouse create/insert/query outputs supplied. Need to load the 6 raw events into the derived table, compare ordinary reading with `FINAL` before assuming merges occurred, and inspect same-version conflicts from the extended fixture. The business invariant that `trade_date` stays stable for the same account/trade remains a necessary data-quality check.
