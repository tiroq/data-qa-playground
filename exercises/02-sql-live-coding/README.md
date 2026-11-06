# Session 02 — SQL Live Coding — Versions, Windows & Deduplication

**Date (Asia/Bangkok):** 2026-11-06 · **Duration:** 90 minutes · **Status:** PLANNED  
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

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
