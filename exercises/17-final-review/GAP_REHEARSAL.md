# Session 17 — Final 60-Minute Readiness Drill

**Rule:** No new infrastructure or long reference solutions. Ask the questions in Russian, one at a time. Do not expose model answers before response. Update only observed gaps.

## 0–15 min — SQL + trade identity

- Given two accounts sharing a trade ID and target retries, state correct physical/logical grain before joining.
- A query returns the correct number of rows but omits `has_failed`. How do you catch incomplete output contracts?
- In a latest-version query, explain why a deterministic physical tie-break does not validate conflicting maximum-version PnL.
- Define what to do when the latest FILLED state has NULL PnL and when no valid latest state can be selected.

## 15–30 min — ClickHouse and streaming

- Explain what `ReplacingMergeTree(version)`, its replacement `ORDER BY`, partition boundaries and `FINAL` do **and do not** guarantee.
- A newly defined insert-triggered MV missed earlier history. Propose a backfill and cutover QA strategy with a rollback trigger.
- Kafka lag=0 and E10 (terminal event) present, but raw sink history lacks E07. What would detect this? What qualifies as actual completion proof?
- Distinguish one immutable event delivered twice from two business updates of the same trade.

## 30–40 min — Async and testing

- For timeout 1.0s and interval 0.4s, choose explicitly whether a predicate call at t=1.0 is permitted, and defend the boundary semantics. The earlier discussion and checked-in implementation differ; **do not pretend there was agreement**.
- Explain why sync blocking sleep inside an async coroutine is a problem and how cancellation should propagate.
- Show a no-empty-PASS test and a case where COUNT equality hides a missing event.
- Explain why an HTTP 202, a committed Kafka offset and a passed unit suite are not end-to-end correctness evidence.

## 40–50 min — Uncertainty, architecture, operational judgment

- Distinguish PASS, FAIL, INDETERMINATE and infrastructure/setup error.
- How would you reconcile historical as-of data when PostgreSQL and ClickHouse snapshots were captured at different source commit positions?
- What is the difference between snapshot PnL and delta PnL under replay?
- Propose one falsifying test for your preferred ClickHouse current-state architecture.

## 50–60 min — Final evidence review

| Gap ID from audit | Independently demonstrated? | Last negative control | Keep open / resolved with evidence |
|---|---|---|---|
| G01 output and grain | | | |
| G02 version ties | | | |
| G03 ClickHouse sorting and partitions | | | |
| G04 completion/as-of | | | |
| G05 timed independent coding | | | |
| G06 no-vacuous-PASS | | | |
| G07 payload/snapshot-vs-delta | | | |
| G08 async deadline contract | | | |
| G09 design versus execution | | | |
| G10 performance/scaling | | | |

Finish with three **grounded** questions for Exness interviewers about trading-data contracts, source/sink reconciliation and testing infrastructure; do not claim knowledge of their internal stack beyond the job description.

References: [readiness audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md), Session 14/15 scorecards (after completion). Mark NOT TESTED for topics not covered.
