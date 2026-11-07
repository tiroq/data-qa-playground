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
