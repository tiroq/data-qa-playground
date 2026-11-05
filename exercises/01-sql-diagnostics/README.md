# Session 01 — SQL Diagnostics & Trading Data Reconciliation

**Date (Asia/Bangkok):** 2026-11-05 · **Duration:** 60 minutes · **Status:** COMPLETED (interactive practice; see verification limitations below)  
**Track:** Exness QA Engineer (Data Stack) interview preparation  
**Difficulty:** SQL fundamentals → reconciliation correctness and edge cases

> **Language contract:** The real Exness technical interview is in **Russian**. All interactive practice, problem discussion, follow-up questions, code review, mock interviews and feedback must be **in Russian**. SQL code, identifiers and ordinary technical terms may remain in English. Repository documentation is in English.

## Goal

Diagnose a small but intentionally inconsistent set of trading records, beginning with basic missing-trade detection and progressing to a complete, one-row-per-business-key reconciliation report.

The main skill being assessed is **turning a business data-quality contract into correct SQL**: business identity, join direction and cardinality, aggregation grain, NULL handling, anomaly precedence, output completeness and meaningful verification. This is the baseline for Sessions 02 (versions/deduplication) and 04 (cardinality-safe reconciliation with time windows).

## Scenario and existing data

The PostgreSQL fixture is installed from [`postgres/init/01-schema.sql`](../../postgres/init/01-schema.sql) and [`postgres/init/02-seed.sql`](../../postgres/init/02-seed.sql).

| Table | Physical grain and relevant columns | Initial rows |
|---|---|---:|
| `trades` (source) | One row per globally unique `trade_id`; also has `account_id`, `symbol`, `volume` | 8 |
| `processed_trades` (target/processing log) | One row per `record_id`; nullable `trade_id`, `account_id`, `status`; repeated composite business keys permitted | 10 |

**Logical matching key for this lab:** `(trade_id, account_id)`. Even though source `trade_id` is currently a primary key, the exercise explicitly validates account identity too.

**Business rule for Session 01:** each source trade is expected to have exactly one processing record. In a real trading lifecycle, multiple attempts or events may be legitimate; the expected record grain must then be redefined before classifying them as duplicates.

The dataset deliberately contains:

- Missing target: source `(106, A3)`.
- Repeated processing rows: `(102, A1)` and `(105, A3)`, two each.
- Failed processing: `(103, A2)` has `FAILED`.
- Unknown status: `(108, A4)` has a real processing record with `status IS NULL`.
- Target-only orphan: `(109, A5)`.

No foreign key or uniqueness constraint on the processing business key is added: invalid records must remain visible for QA diagnostics.

## Setup and reproducibility

From the repository root:

```bash
docker compose up -d --wait
docker compose exec postgres psql -U qa -d trading
```

Use `\dt`, `SELECT * FROM trades;` and `SELECT * FROM processed_trades;` to inspect the schema and data.

Run the existing **initialization smoke check** (not an exercise solution):

```bash
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 -f /dev/stdin < postgres/checks/smoke.sql
```

The smoke check asserts 8 source rows and 10 processing rows; it does **not** prove correctness of any reconciliation solution. When modifying fixture data manually, restore the baseline with `docker compose down -v` followed by `docker compose up -d --wait` (**destructive to the local PostgreSQL volume**).

## Practical assignment

### Exercise 1 — Missing Trades Detection

Return source trades that have **no matching processing row**. Required output: `trade_id`, `account_id`, `symbol`.

1. Explain which side of the join must be preserved and why `INNER JOIN` is unsuitable.
2. Match on the declared composite business key, not merely a convenient identifier.
3. Distinguish an **absent target row** from an existing row with `FAILED` or `NULL` status.
4. Explain why duplicate matching target rows must not generate extra missing-trade rows.

Expected baseline anomaly: `(106, A3)`.

See [the original and revised SQL attempts](01-missing-trades.sql) and [design rationale / reference SQL](01-missing-trades.md). An additional exploratory version is stored as [`01-missing-trades.upd.sql`](01-missing-trades.upd.sql); note that its trade-id-only join is **not equivalent** to the declared composite-key contract if IDs can be reused or corrupted across accounts.

### Exercise 2 — Duplicate Processing Detection

Find business keys represented by **more than one physical processing row**. Required output: `trade_id`, `account_id`, `processing_count`.

1. Select from the processing table so target-only duplicate keys are not hidden by an inner join to source.
2. Group by the full business key, not by `status`, `record_id` or descriptive attributes.
3. Explain `COUNT(*)` vs `COUNT(status)`, `WHERE` vs `HAVING` and `NULL`-key grouping.
4. Distinguish a repeated processing row from a legitimate version or lifecycle transition (outside this simplified contract).

Expected baseline anomalies: `(102, A1, 2)` and `(105, A3, 2)`.

See [the original attempt](02-duplicate-processing.sql), [revised attempt](02-duplicate-processing.upd.sql) and [design rationale / reference SQL](02-duplicate-processing.md).

### Exercise 3 — Full Trading Data Reconciliation

Produce **one row per valid logical business key**, preserving both source-only and target-only identifiers.

Required output:

| Column | Contract |
|---|---|
| `trade_id`, `account_id` | Full composite business identity, retained for both matched and unmatched rows |
| `processing_count` | Count of real processing records; **0** for missing source trades |
| `has_failed` | Independent boolean flag when any actual processing row has `FAILED` |
| `has_unknown` | Independent boolean flag when any actual processing row has `status IS NULL` |
| `dq_status` | One headline category according to the precedence below |

**Headline precedence:** `ORPHAN > MISSING > DUPLICATE > FAILED > UNKNOWN > OK`.

The flags are independent of `dq_status`: e.g., a duplicate key may also have a failed processing attempt, and neither fact should be discarded.

1. Use a `FULL JOIN` or a sound equivalent to preserve both directions of discrepancies.
2. Use `COALESCE` to retain identifiers on unmatched rows, with an explicit policy for invalid/NULL business keys.
3. Aggregate **at the business-key grain**, not by individual processing status.
4. Use `COUNT(processed.record_id)` (rather than joined `COUNT(*)`) for correct zero counts after an outer join.
5. Guard unknown-status detection with **target-row presence**, because the synthetic NULL side of an outer join is not a genuine unknown processing status.
6. Ensure all **six required output columns** appear, with deterministic ordering for reproducible checks.

Expected baseline: **9 distinct valid business keys**; statuses are `OK` (101, 104, 107), `DUPLICATE` (102, 105), `FAILED` (103), `MISSING` (106), `UNKNOWN` (108), `ORPHAN` (109).

See [the original attempt](03-full-reconciliation.sql), [revised attempt](03-full-reconciliation.upd.sql) and [design rationale / reference SQL](03-full-reconciliation.md).

**Important review note:** The revised `03-full-reconciliation.upd.sql` calculates `has_failed` inside its CTE but **does not include it in the final SELECT**. The reference walkthrough includes the full required output. The attempt files are intentionally retained as history, not silently rewritten into reference solutions.

## Discussion extension — time-based SLA (not implemented in the baseline schema)

Hypothetical contract: **at least 95% of eligible trades must appear in the processed system within 10 minutes of creation**. For a defined eligible population of 100,000 trades, if 80 are late, then:

- Late share = `80 / 100000 = 0.08%`.
- On-time share = `99920 / 100000 = 99.92%`.
- **Aggregate SLA passes** despite individual late records.

Explain eligibility, data cutoffs, missing timestamp policy, in-flight records, zero denominators, event time vs processing time and late-arrival false alarms. These are conceptual interview follow-ups: **the Session 01 tables have no creation/processing timestamps**, so no executable 10-minute SLA computation is claimed here. Later sessions introduce richer schemas and evaluation windows.

## Contracts and constraints

- Treat this dataset as synthetic training data, not Exness production schema or policy.
- Keep original Session 01 schema, seed and historical SQL attempts unchanged.
- Composite-key integrity and row-presence indicators take priority over apparently convenient status checks.
- Do not allow joins to hide target-only records or multiply aggregates without detection.
- Nullable processing keys are **invalid identity data** and should be reported separately rather than assumed to match valid trades.
- An observed status is not automatically a business conclusion; specify the record grain and lifecycle contract.

## Acceptance criteria and observed outcome

- [x] Identify the missing source trade under the declared composite key.
- [x] Detect duplicate processing groups at the intended business grain.
- [x] Explain why `FAILED` and `NULL` status do not imply missing records.
- [x] Recognize the need for `FULL JOIN`, non-null row-presence indicators, `COUNT(record_id)` and grouped DQ flags.
- [x] Correct the initial error of grouping reconciliation rows by `status`.
- [ ] Include **every required output field** in the final submitted reconciliation SQL (`has_failed` is missing from the outer `SELECT`).
- [ ] Record an actual executable test result for each of the three SQL attempts; only the source files and explanatory references are presently preserved here.
- [ ] Extend reconciliation to genuinely duplicated source keys and time-window eligibility (later sessions).

## Session artifacts

| Type | Files |
|---|---|
| Setup | [PostgreSQL schema](../../postgres/init/01-schema.sql), [seed](../../postgres/init/02-seed.sql), [smoke check](../../postgres/checks/smoke.sql) |
| Missing trades | [Attempt](01-missing-trades.sql), [exploratory variant](01-missing-trades.upd.sql), [reference rationale](01-missing-trades.md) |
| Duplicates | [Attempt](02-duplicate-processing.sql), [revised attempt](02-duplicate-processing.upd.sql), [reference rationale](02-duplicate-processing.md) |
| Full reconciliation | [Attempt](03-full-reconciliation.sql), [revised attempt](03-full-reconciliation.upd.sql), [reference rationale](03-full-reconciliation.md) |
| Miscellaneous | [Query scratchpad](query-all.sql) |

Reference walkthroughs contain solutions **because this session has already been completed**. Reattempting under strict mock conditions requires not opening the reference files until after answering.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — строгий технический интервьюер Exness QA Engineer (Data Stack). Реальное техническое интервью 16 ноября 2026 года проходит **на русском языке**. Проведи сессию 01 «SQL Diagnostics & Trading Data Reconciliation» (60 минут). **Все вопросы, объяснения, обсуждения SQL-запросов и обратная связь — только на русском**; синтаксис SQL и технические термины можно оставлять на английском. Мой опыт — Python/Go SDET, trading/FIX/post-trade, reconciliation, CI, NATS JetStream. Открой через GitHub репозиторий `tiroq/data-qa-playground` и этот файл `exercises/01-sql-diagnostics/README.md`. Используй три задания и критерии приёмки из README. Поскольку занятие уже пройдено и в репозитории есть эталонные SQL, **не открывай их и не раскрывай ответы до моей самостоятельной попытки**. Начни с Exercise 1, дождись SQL и объяснения. Задавай follow-up по составному ключу, NULL, JOIN cardinality, группировке, полноте выходных колонок и SLA. После каждого решения оцени корректность и edge cases; в конце дай оценку /10 и три конкретных направления улучшения.

## Session result — review summary

- **Status:** Completed as an interactive learning session on 2026-11-05. Historical SQL attempts and revised queries are committed; this README is the retrospective.
- **Indicative coaching score:** approximately **9/10** overall; this is an informal discussion-based assessment, **not** a benchmark or automated-test result.
- **What worked:** composite business keys, anti-join reasoning, `GROUP BY`/`HAVING`, distinguishing missing from failed/unknown, reconciliation classification and percentage-based SLA reasoning.
- **Corrections made:** initial full-reconciliation grouping by raw status fragmented logical trade keys; aggregation was revised toward business-key-level flags.
- **Known gap remaining in the submitted SQL:** the final revised reconciliation query omitted required `has_failed` from its output.
- **Next-session adjustments:** (1) window functions, version ties and deduplication; (2) aggregation-before-join and explicit cardinality testing; (3) strict checking of required output fields, NULL edge cases and repeatable verification.

Continue from [Session 02 — SQL Live Coding](../02-sql-live-coding/README.md), then [Session 04 — Reconciliation](../04-reconciliation/README.md).
