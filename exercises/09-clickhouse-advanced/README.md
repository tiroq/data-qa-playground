# Session 09 — ClickHouse Advanced — MV, TTL & Backfill

**Date (Asia/Bangkok):** 202026-11-11 **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Goal

Validate schema evolution, aggregates and recovery in an analytical pipeline.

## Practical assignment

1. Design a raw-event table and a derived materialized view with explicit state and version semantics.
2. Propose validation for aggregations, TTL retention, distributed queries and delayed merges.
3. Plan a schema migration with backfill/replay, dual-write or shadow comparison and rollback.
4. Explain why changing a materialized view does not automatically reprocess historical data.

## Contracts and constraints

- Business correctness is independent of physical merge timing.
- Retention must not erase the only source needed to reconstruct derived tables.
- Backfill should be idempotent and reconciliation must compare compatible windows.

## Acceptance criteria

- [ ] Migration plan includes before/after invariants and a rollback decision.
- [ ] Explains count vs distinct trade count vs latest-state count.
- [ ] Includes a query-level consistency check under duplicate delivery.

## Artifacts to add **during** this session

- Incremental ClickHouse DDL and verification queries
- Migration/backfill runbook and review notes

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 09: «ClickHouse Advanced — MV, TTL & Backfill» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/09-clickhouse-advanced/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
