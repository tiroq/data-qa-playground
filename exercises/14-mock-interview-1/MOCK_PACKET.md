# Session 14 — Unseen Timed Mock Packet: SQL, Python and Testing

**Moderator instruction:** keep this packet closed until the interview timer starts. Do not expose solutions or give leading hints. Interview and explanations in **Russian**, code in SQL/Python. The purpose is to test independent performance against previously observed gaps, **not** familiarity with reference files.

**90-minute distribution:** SQL 35m, Python 30m, pytest/quality follow-ups 15m, scoring 10m.

## A — SQL (35 min)

**Scenario:** PostgreSQL source and analytics target receive versions of the same trade. Each physical delivery has `delivery_id`, `event_id`, `trade_id`, `account_id`, `version`, `pnl`, `status`, and `observed_at`. Composite business key is `(trade_id, account_id)`; PnL is a current-state snapshot, not a delta.

Source deliveries:

| delivery_id | event_id | trade | account | version | pnl | status |
|---|---|---|---|---|---|---|
| S1 | E101 | X1 | A1 | 1 | 0.00 | NEW |
| S2 | E102 | X1 | A1 | 2 | 10.00 | FILLED |
| S3 | E102 | X1 | A1 | 2 | 10.00 | FILLED |
| S4 | E201 | X2 | A1 | 1 | 4.50 | FILLED |
| S5 | E301 | X3 | A2 | 2 | 7.00 | FILLED |
| S6 | E302 | X3 | A2 | 2 | 8.00 | FILLED |
| S7 | E401 | X4 | A2 | 1 | NULL | FILLED |

Target contains source rows S1,S2,S4,S5 and an additional row E501/X5/A3/v1/3.00/FILLED. Assume query visibility for each target row occurred before a declared cutoff; later use independent time windows to challenge this assumption.

**Tasks (do not give an answer):**

1. Write latest defensible trade-state SQL with explicit conflict handling. Required columns: `trade_id, account_id, latest_version, latest_status, latest_pnl, is_ambiguous`. State the output grain and tie policy.
2. Write a cardinality-safe full reconciliation preserving keys on either side. Required columns: `trade_id, account_id, source_physical_count, target_physical_count, latest_version_mismatch, has_payload_conflict, dq_status`. State which flags are NOT_EVALUATED when versions differ.
3. Explain one data-quality counterexample to your approach without using a mentor answer. Explain how to test output column completeness and nullable PnL.

**Interview constraint:** a candidate can ask about event identity, snapshot contract or business status, but cannot assume unspecified version ties have a valid winner.

## B — Python (30 min)

Implement on a blank page: `compare_event_ids(expected: list[str], actual: list[str], *, planned_count: int)` returning **independent** missing IDs, unexpected IDs, physical duplicates and a validation error for an unexpectedly empty/invalid expected manifest.

Then extend the design verbally to detect conflicting payloads of identical `event_id`, current versions and conflicting PnL. Explain time complexity and memory. Challenge with (a) duplicate hides missing and (b) an input containing 50,000 versions of one trade.

**Do not open the Session 05 reference implementation until after the independent submission.**

## C — Pytest / DQ follow-ups (15 min)

- Design a fixture that guarantees no cross-test leaked committed DB rows and explain when rollback is insufficient.
- Explain what Kafka committed offset and API HTTP 202 can prove, and what they cannot.
- Distinguish PASS, FAIL and INDETERMINATE for an unexpectedly empty source manifest.

## D — Scoring (10 min)

Use [SCORECARD_TEMPLATE.md](SCORECARD_TEMPLATE.md). Freeze original answers first; evaluate completeness, actual reasoning and three observed gaps. No code modifications masquerading as the original answer.

**Source of targeted questions:** [readiness audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md), gaps G01,G02,G05,G06,G10. These are new synthetic exercise rows, not an assertion about Exness' actual schema.
