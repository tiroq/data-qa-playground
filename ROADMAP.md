# Exness Data QA Preparation — 17-Session Roadmap

**Target interview:** 2026-11-16, Russian-language technical interview for QA Engineer (Data Stack).  
**Approach:** One continuously evolving **synthetic trading-data QA case**, not 17 isolated solutions. Repository specifications and code are in English; interactive discussion and assessment are in Russian.

## Status semantics

- **COMPLETE:** a real attempt and review exist in the repository.
- **PLANNED:** exercise specification only. No claim of an implemented solution.
- **IN PROGRESS:** a linked branch or PR contains a current attempt.
- **REVIEWED:** acceptance criteria and a recorded score have been checked.

## Timeline and cumulative value

| # | Date (Bangkok) | Session | Status | Contribution to case |
|---|---|---|---|---|
| 01 | Nov 05 | [SQL diagnostics](exercises/01-sql-diagnostics/) | COMPLETE (learning session) | Existing PostgreSQL tables, SQL examples and detailed rationale |
| 02 | 11 06 | [SQL Live Coding — Versions, Windows & Deduplication](exercises/02-sql-live-coding/README.md) | PLANNED | Latest-version selection and account PnL |
| 03 | 11 06 | [ClickHouse Fundamentals — MergeTree & Row Semantics](exercises/03-clickhouse-fundamentals/README.md) | PLANNED | ClickHouse storage semantics |
| 04 | 11 07 | [Source-to-Target Reconciliation & SLA](exercises/04-reconciliation/README.md) | PLANNED | Cardinality-safe reconciliation and timing SLA |
| 05 | 11 08 | [Python Live Coding — Streaming Comparison](exercises/05-python-live-coding/README.md) | PLANNED | Python comparison core |
| 06 | 11 08 | [Data Quality — Contracts, Gates & Metrics](exercises/06-data-quality-rules/README.md) | PLANNED | DQ rules and severity |
| 07 | 11 09 | [Pytest Architecture — Fixtures & Isolation](exercises/07-pytest-architecture/README.md) | PLANNED | Pytest and containerized isolation |
| 08 | 11 09 | [Async Testing — Eventual Consistency](exercises/08-async-testing/README.md) | PLANNED | Eventual-consistency testing |
| 09 | 11 10 | [ClickHouse Advanced — MV, TTL & Backfill](exercises/09-clickhouse-advanced/README.md) | PLANNED | ClickHouse MV/migrations/backfill |
| 10 | 11 10 | [SQL Mock Interview — Correctness Under Time Pressure](exercises/10-sql-mock/README.md) | PLANNED | Timed SQL assessment |
| 11 | 11 11 | [Kafka / Flink — Streaming Failure Modes](exercises/11-kafka-flink/README.md) | PLANNED | Streaming delivery/replay invariants |
| 12 | 11 12 | [Trading Data Pipeline Design — End-to-End QA](exercises/12-pipeline-design/README.md) | PLANNED | End-to-end design and test matrix |
| 13 | 11 12 | [Quality Gates & CI — Reproducible Data Testing](exercises/13-quality-gates-ci/README.md) | PLANNED | CI quality gates |
| 14 | 11 13 | [Mock Interview 1 — SQL, Python & Testing](exercises/14-mock-interview-1/README.md) | PLANNED | Timed coding mock |
| 15 | 11 14 | [Mock Interview 2 — ClickHouse, Streaming & Incident QA](exercises/15-mock-interview-2/README.md) | PLANNED | Production/streaming mock |
| 16 | 11 14 | [Experience Stories — Evidence-Based Interview Answers](exercises/16-experience-stories/README.md) | PLANNED | Verified STAR stories |
| 17 | 11 15 | [Final Review — Confidence & Gaps](exercises/17-final-review/README.md) | PLANNED | Final revision sheet |

Session 01's existing solutions and explanations are preserved as historical learning artifacts; the new session READMEs intentionally contain no reference solutions.

## Incremental implementation strategy

1. **Baseline — existing and runnable:** `compose.yaml` boots PostgreSQL; `postgres/init/` creates and seeds `trades` and `processed_trades`; `postgres/checks/smoke.sql` checks the seed; Session 01 holds the diagnostics.
2. **SQL extension:** Session 02 has an isolated `lab02.trade_versions` fixture; write SQL in session-specific files only after solving. Session 04 adds a separate source-duplicate/late-arrival fixture rather than modifying Session 01 seed.
3. **Python test core:** Starting Session 05, introduce `src/data_qa/`, `tests/unit/`, and `pyproject.toml` only alongside working code/tests; grow toward reconciliation, quality rules and async polling.
4. **Analytical/storage layer:** Add ClickHouse service(s), DDL, data-load tasks and checks during Session 03 and enhance them in Session 09.
5. **Streaming layer:** Add Kafka/Flink or a lightweight reproducible event simulator during Session 11 only if exercise time permits. Document which transport guarantees are simulated vs proven.
6. **Quality gate:** Integrate reproducible tests into CI in Session 13. A passing check must prove required data existed and expected invariants held.
7. **Evidence and review:** Each completed session adds its attempt, objective observations, edge-case tests, notes, score and next actions. Mock interviews do not overwrite working implementations.

## Definition of done for a session

- [ ] Actual attempt exists (SQL/code/design notes or mock answers).
- [ ] Expected output grain and business contract are explicit.
- [ ] At least one failing/edge case was tested or deliberately documented.
- [ ] Verification command and observed result are recorded; no invented CI status.
- [ ] A score, three weaknesses and follow-on actions are recorded.
- [ ] `ROADMAP.md` status is updated based on evidence, not on time elapsed.

## End-state acceptance

A reviewer should be able to bootstrap PostgreSQL; inspect case contracts; run independent SQL/data-quality checks; run implemented Python tests; and understand clearly which ClickHouse/Kafka/Flink capabilities are runnable, simulated or only designed. The educational objective is **defensible reasoning about trading-data correctness**, not an artificially inflated stack.
