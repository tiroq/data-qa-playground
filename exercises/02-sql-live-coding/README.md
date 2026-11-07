# Session 02 — SQL Live Coding — Versions, Windows & Deduplication

**Date (Asia/Bangkok):** 2026-11-06 · **Duration:** 90 minutes (planned) · **Status:** IN PROGRESS — interview exercises reviewed; runtime verification pending  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Select the latest defensible trade state without losing valid trades or inflating PnL.

## Practical assignment

1. Inspect `lab02.trade_versions` created by the supplied fixture. State its **physical row grain** and the proposed **logical trade grain** before writing SQL.
2. Return the latest record for each `(trade_id, account_id)` using a window function. Define deterministic tie-breaking for equal versions and explain whether ingestion time is authoritative.
3. Compute account-level latest PnL using `NUMERIC`, ensuring retries and older versions are not double-counted.
4. Explain how PostgreSQL `DISTINCT ON` differs from portable `ROW_NUMBER()`, then outline ClickHouse `argMax` and the risk of non-deterministic ties.

## Contracts and constraints

- The original `trades` and `processed_trades` tables remain unchanged.
- `ingest_id` identifies stored rows; repeated business keys represent retries/versions, not necessarily extra trades.
- A tie on `version` must be handled explicitly; a later `ingested_at` is not always a later business event.

## Setup

The isolated `lab02` fixture is loaded automatically by the one-shot `postgres-lab02-init` service whenever you run `docker compose up -d --wait`, even if the PostgreSQL volume already exists. Run `docker compose wait postgres-lab02-init` to ensure the loader has exited. Verify its output with `docker compose logs postgres-lab02-init` and check row counts:

```bash
docker compose exec -T postgres psql -U qa -d trading -c "SELECT COUNT(*) AS physical_rows, COUNT(DISTINCT (trade_id, account_id)) AS logical_keys FROM lab02.trade_versions;"
```

Expected initial fixture: **12 physical rows and 6 logical keys**. The loader is idempotent; `docker compose restart postgres` does not rerun it.

## Acceptance criteria

- [ ] Exactly one logical latest-state row per `(trade_id, account_id)` under the chosen policy.
- [ ] All output columns named in the task are returned; stable ordering is stated.
- [ ] Explain the handling of duplicate deliveries, version ties, `NULL` status and late arrival.
- [ ] Compare at least two SQL formulations, including trade-offs.

## Artifacts to add **during** this session

- `solutions/02-latest-trades.sql` (created during the session, not prefilled)
- `notes/02-sql-review.md` with correctness and edge-case analysis

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 02: «SQL Live Coding — Versions, Windows & Deduplication» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/02-sql-live-coding/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (interview debrief)

- **Candidate attempts:** [ROW_NUMBER initial](solutions/02-latest-trades.sql), [ROW_NUMBER follow-up](solutions/02-latest-trades-followup.sql), [account PnL initial](solutions/02-account-pnl-attempt.sql), [DISTINCT ON](solutions/03-distinct-on-attempt.sql).
- **Mentor reference / explanations (not independently solved by learner):** [latest trade](solutions/02-latest-trades-reviewed.sql), [account PnL](solutions/02-account-pnl-reviewed.sql), [SQL alternatives](notes/03-sql-alternatives.md).
- **Overall learning assessment:** **7.5/10** (qualitative, not a benchmark or a verified runtime score). Task 1: 7.5/10; Task 2: 6/10 (mentor walkthrough required); Task 3: DISTINCT ON SQL 9.5/10, conceptual PostgreSQL comparison 8/10, ClickHouse argMax reasoning 9/10.
- **What worked:** correct logical grain and latest-version precedence, deduplication before aggregation, correct PostgreSQL DISTINCT ON order prefix, sound reasoning about late arrivals, correct concern about argMax ties and cross-column consistency.
- **Three priority gaps:** (1) distinguish window ranking order from query/CTE result order; (2) detect contradictory payloads among all rows of the highest version **before** reducing to one row and block unverified PnL; (3) strengthen ClickHouse argMax tuple and NULL handling, plus business-authoritative tie-breaker policy.
- **Edge cases documented:** duplicate deliveries (201), out-of-order ingestion (203), NULL status/PnL (204), contradictory same-version PnL (205), and missing/empty cohorts.
- **Runtime verification:** **NOT DONE**. No PostgreSQL or ClickHouse execution or observed outputs were provided. The fixture predicts 12 physical rows / 6 logical keys; the mentor's account summary predicts A1 2/5.5000/false, A2 1/9.0000/false, A3 1/NULL/true. Predictions are not passing tests.
- **Next-session adjustments:** short hands-on replay of trade conflict detection, ClickHouse argMax semantics and syntax, and an actual recorded SQL execution on the fixture.
- **Remaining completion gate:** execute reference SQL against PostgreSQL, confirm observed results, and record evidence before moving status to COMPLETE/REVIEWED.
