# Session 03 — ClickHouse Fundamentals — MergeTree & Row Semantics

**Date (Asia/Bangkok):** 2026-11-06 (scheduled) · **Duration:** 60 minutes · **Status:** IN PROGRESS — local ClickHouse fixture prepared; runtime and candidate work pending  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Understand ClickHouse storage and why physical duplicates do not automatically disappear in analytical queries.

## Practical assignment

1. Explain the purpose and trade-offs of `MergeTree`, `ReplacingMergeTree(version)`, `ORDER BY`, primary-key index and `PARTITION BY` for trading events.
2. Design a minimal ClickHouse table for the versioned events from Session 02 without changing the PostgreSQL fixture.
3. Predict query outputs before and after background merges; determine when `FINAL` or query-time latest-version aggregation is needed.
4. Describe a verification strategy for ingest count, deduplication and query correctness.

## Contracts and constraints

- A merge is asynchronous; never assume the visible row count immediately reflects deduplication.
- ClickHouse `ORDER BY` is a storage sorting key, not a PostgreSQL-style UNIQUE constraint.
- The target schema and chosen replacement key must be justified against the declared grain.

## Setup

An optional ClickHouse profile and two raw fixtures have now been added; PostgreSQL remains the default service. See [the lab guide](../../clickhouse/README.md). Start the ClickHouse service without touching PostgreSQL:

```bash
docker compose --profile clickhouse up -d --wait clickhouse
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/smoke.sql
docker compose --profile clickhouse exec clickhouse clickhouse-client --user qa --password qa --database lab03
```

The supplied `lab03.trading_events` is an **append-only raw input** with six physical rows, not the learner's requested deduplicating table. `lab03.trade_versions` mirrors the 12 PostgreSQL Session 02 events. Create a separate derived table when attempting the `ReplacingMergeTree` part. Counts are expectations until tested on the learner's Docker host.

## Acceptance criteria

- [ ] Can explain why two correct-looking queries may return different totals.
- [ ] Proposes test data including retries, version ties and delayed merges.
- [ ] Lists when `FINAL` is expensive or operationally unsuitable.

## Artifacts to add **during** this session

- `clickhouse/README.md` or SQL notes when implemented in this session
- `notes/03-clickhouse-review.md` with observed behaviour

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 03: «ClickHouse Fundamentals — MergeTree & Row Semantics» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/03-clickhouse-fundamentals/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
