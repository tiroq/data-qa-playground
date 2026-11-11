# Exness Data QA Interview — Readiness Audit (2026-11-11)

**Interview:** 2026-11-16, 17:00 Bangkok, conducted in Russian.  
**Sources of evidence:** checked-in candidate attempts, guided notes, source code, test assets, GitHub Actions runs linked below, and the recorded interactive discussion.  
**Purpose:** use completed learning sessions 01–08 to make remaining sessions 09–17 diagnostically targeted. This is **not a new performance score** and does not certify abilities that were only demonstrated by assistant-authored reference code.

## Evidence language

- **Learner attempt:** answer/code actually proposed during the interview practice.
- **Guided/reference implementation:** produced after discussion, but not independent candidate coding evidence.
- **Runtime verification:** executed test/CI evidence for a particular code revision and scope; not an end-to-end production guarantee.
- **Oral evidence:** understanding demonstrated in discussion, not a timed implementation.
- **Open:** not sufficiently verified to claim mastery or acceptance.

## Session-by-session review

| Session | Demonstrated strengths | Specific issues / unverified aspects | Status and evidence |
|---|---|---|---|
| **01 SQL diagnostics** | Correct use of business keys, anti-join logic, duplicate GROUP BY/HAVING, FULL JOIN classification, distinguishing MISSING from FAILED | Original reconciliation grouped on status; revised output omitted mandatory `has_failed`; exact SQL assertions have not been run as a completed end-to-end verification | Learning session complete; see [Session 01 README](../exercises/01-sql-diagnostics/README.md) and original SQL |
| **02 SQL live coding** | `ROW_NUMBER()` with composite grain; late older version recognized; `DISTINCT ON` candidate attempt reviewed positively | Window tie-breaker initially absent; outer ORDER BY confused with window ORDER BY; account PnL attempted with wrongly defined `has_conflict`, grouped at account+flag rather than account; reference was mentor-authored; runtime SQL unverified | Exercises discussed; Task 1 7.5/10, Task 2 6/10, Task 3 DISTINCT ON 9.5/10 are **scoped static reviews**, not final score; see [notes](../exercises/02-sql-live-coding/notes/02-sql-review.md) |
| **03 ClickHouse fundamentals** | Recognized double-counting of physical versions; understood stable partition key after follow-up; queried raw-versus-latest design and retention | Initially used `ORDER BY (account_id, trade_id, version)` as replacement key; early DDL lacked `ReplacingMergeTree(version)` and stable partitioning; `argMax` tie/conflict, `FINAL`/merges and MV design not independently runtime proven | Guided conceptual and DDL attempts; no blanket claim of independent mastery or executed query. [Review notes](../exercises/03-clickhouse-fundamentals/notes/03-clickhouse-review.md) |
| **04 Reconciliation** | Independent source/target aggregation before join, nullable diagnostics, status versus delivery, historical as-of, different versions and SLA eligibility reasoning | SQL implementation is guided/interviewer-authored; executable assertions have not been shown as verified. Snapshot cutoffs, watermark and completion barriers require stronger independent proof | Guided design and SQL drafts; [review](../exercises/04-reconciliation/notes/04-reconciliation-review.md), [fixture](../exercises/04-reconciliation/sql/01-fixture.sql) |
| **05 Python live coding** | Typed `Record`/`TradeGroup`/`TradeResult`, checker chain, `latest()`, batch `compare_events`, malformed-record coverage, Decimal and deterministic output; implementation is present and CI has passed a Session 05 test revision | Older START_HERE and review note still describe an unimplemented starter, now stale. Reference/assisted implementation should not be scored as independent timed coding. Check complexity: current checker version scans can approach O(V×M), up to quadratic, per trade; no true streaming algorithm or end-to-end time cutoff | Implemented and unit-tested, **independent interview grade pending**. [Implementation notes](../exercises/05-python-live-coding/IMPLEMENTATION.md); [Session 05 CI](https://github.com/tiroq/data-qa-playground/actions/runs/42825189862) |
| **06 Data Quality** | 20 independently responsible rules, distinction between event ID / business key / version, explicit PASS/FAIL/INDETERMINATE, manifest-based completeness and SLA bounds; isolated checkers and tests | Define what evidence suffices to promote INDETERMINATE, own SLO thresholds, detect missing authoritative manifest, and prove negative controls per gate; 20 rules are not all a single fully integrated production gate | In progress: rules implemented, policy review pending. [Catalog](../exercises/06-data-quality-rules/docs/data-quality-rules.md) |
| **07 Pytest architecture** | Real PostgreSQL and ClickHouse Testcontainers, localhost HTTP and real two-partition Kafka teaching tests; fixture cleanup, isolation, set+Counter manifest, payload anomalies; integration CI successful | The HTTP queue and Kafka broker are separate controlled boundaries, not one deployed production pipeline; no real per-partition post-sink completion service, consumer rebalance or Flink job; weighted xdist scheduling is design only | Lab COMPLETE at documented synthetic/test-system scope; [coverage](../exercises/07-pytest-architecture/TEST_COVERAGE.md), [integration CI](https://github.com/tiroq/data-qa-playground/actions/runs/42826563119) |
| **08 Async testing** | Oral reasoning about monotonic bounded polling, retries with allowlisted exceptions, last-observation diagnostics, sync versus async, cancellation and replay/idempotency distinction; code and deterministic tests committed | Written reference code is assistant-authored and is **not** timed learner code evidence; there is no independently confirmed CI run of Session 08-specific test file. **Unresolved contract discrepancy:** conversation considered polling at t=1.0 (fourth call for 1.0s/0.4s), while checked-in tests expect t=0/0.4/0.8 only (three calls) | Oral score recorded as 8/10; code/test verification separately pending. [README](../exercises/08-async-testing/README.md), [tests](../exercises/08-async-testing/test_wait_until.py) |

## Highest-priority gaps and targeted interview drills

| Gap ID | Risk / counterexample to expose | Priority | Where to probe |
|---|---|---|---|
| **G01 — Output and grain** | Correct-looking SQL drops a mandatory field, or groups at `account_id + status` rather than one account | HIGH | 10, 14, 17 |
| **G02 — Version ties before collapse** | `ROW_NUMBER` / `argMax` hides same-max-version contradictory PnL | HIGH | 09, 10, 14, 15 |
| **G03 — ClickHouse replacement and partitions** | Version included in replacement `ORDER BY`, or versions partitioned across mutable months; `FINAL` misinterpreted | HIGH | 09, 15 |
| **G04 — As-of / SLA eligibility** | Treating lag=0/watermark/last event as sink completion; inconsistent snapshots produce false MISSING/TARGET_AHEAD | HIGH | 11, 12, 13, 15 |
| **G05 — Independent coding under time pressure** | Strong coached explanation but absent independent 20-minute solution and self-test | HIGH | 10, 14 |
| **G06 — No-vacuous-PASS and uncertainty** | `0 == 0` or missing manifest reported PASS; INDETERMINATE incorrectly becomes PASS | HIGH | 13, 14, 17 |
| **G07 — Physical identity vs payload and PnL** | Matching counts or event IDs hide loss/corruption; snapshot PnL confused with delta PnL | HIGH | 11, 12, 15 |
| **G08 — Async deadline contract** | Exact deadline boundary unclear, cancellation swallowed, retrying writes rather than reads | MEDIUM | 14, 17 |
| **G09 — Execution proof vs design proof** | CI green for helper/fixture mistakenly treated as end-to-end data integrity or Kafka/Flink guarantees | HIGH | 11, 13, 15, 17 |
| **G10 — Performance/scaling** | In-memory comparison remains quadratic for many versions; `FINAL` or MV query costs unquantified | MEDIUM | 09, 12, 14 |

## Important documented discrepancies

1. **Session 05 metadata was stale:** `README.md` and `notes/05-python-review.md` may still call the implementation pending, but source code and a successful historical Session 05 CI run exist. Distinguish existence of implementation from who independently coded every part.
2. **Session 08 polling boundary is an explicit contract decision:** the learner considered a fourth predicate call at the exact t=1.0 deadline; the recorded reference contract forbids beginning that call. Do not rewrite this disagreement away: require the learner to choose a contract, test both policies and explain the trade-off.
3. **Session 03 and Session 07 ClickHouse evidence differs:** conceptual questions and older session notes saying "no SQL executed" may remain true for *those learner attempts*, even while separate later Session 07 real ClickHouse integration tests passed. Never retroactively attribute reference integrations as learner-authored Session 03 DDL.
4. **Production versus controlled lab:** the successful real Kafka and ClickHouse Testcontainers jobs prove their specific negative controls, not a real Flink pipeline or end-to-end exactly-once.
5. **Existing Session 08 tests are not in the `lab-readiness` workflow.** Do not infer they ran from unrelated workflow success.

## Minimum acceptance criteria for remaining sessions

- Candidate states **grain, business invariants, required outputs, version/tie rule, source of truth, and cutoff** before giving code or architecture.
- At least one falsifying example and one negative control, not only a happy path.
- For SQL: check cardinality, all required columns, NULL and tie semantics, and whether the output remains one row per declared grain.
- For Kafka/ClickHouse: separate persisted raw IDs, logical latest state, sink progress, and transient in-flight data.
- For CI: an unexpectedly empty or unverified cohort is FAIL/INDETERMINATE, never green by default.
- After each mock: preserve initial attempt, record observed score and three concrete priorities. Do not promote reference-answer familiarity to independent mastery.
- **Session 09 remains unattempted** as of this audit. Its answers will be collected only after the separate oral conversation.

## Work allocation (no calendar changes)

- **09:** one-question-at-a-time oral ClickHouse follow-ups, no prewritten SQL solutions.
- **10:** independent timed SQL; no hints before submission.
- **11–12:** streaming and architecture, especially sink-side evidence and history/replay contracts.
- **13:** negative controls, manifest/SLA and CI evidence.
- **14–15:** two full mocks targeting gaps; do not replace with generic tutorials.
- **16:** three verifiable personal experience stories; avoid invented metrics.
- **17:** concise final rehearsal, not new infrastructure.
