# Session 02 — SQL Live Coding — Review Notes

**Date:** 2026-11-06 (Asia/Bangkok)  
**Status:** IN PROGRESS — awaiting candidate follow-up; no reference solution included.  
**Attempt:** [initial candidate SQL](../solutions/02-latest-trades.sql)  
**Preliminary score for Task 1:** 7/10 (subject to follow-up and execution-based checks). This is **not** the final session score.

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

### Follow-up (pending candidate)

- Modify the submitted query to make selection reproducible under equal `version` and make final output ordering stable.
- Explain the chosen tie-breaking policy and whether `ingested_at` can be treated as business-authoritative.
- State how the QA pipeline should handle trade 205 conflicting same-version PnL, separately from its SQL row-selection rule.

### Verification evidence

- **Static review only.** No live PostgreSQL query, `docker compose` run, or result-row assertion has been performed in this review.
- Fixture expectations from checked-in SQL: 12 physical rows, 6 logical keys.
- Final score, reference approach, edge-case tests, and roadmap update **pending** candidate follow-up and verification.
