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
