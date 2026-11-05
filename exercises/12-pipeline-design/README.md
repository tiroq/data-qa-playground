# Session 12 — Trading Data Pipeline Design — End-to-End QA

**Date (Asia/Bangkok):** 2026-11-12 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Connect the accumulated SQL, reconciliation and Python testing into an end-to-end design.

## Practical assignment

1. Design Kafka → processing/Flink → ClickHouse → API with PostgreSQL or an upstream source of truth.
2. Define event schema, ownership, data contracts, logical grain, idempotency policy and schema evolution.
3. Create a layered testing strategy from unit checks to production reconciliation and monitoring.
4. Stress-test replay, backfill, duplicate events, out-of-order updates, delayed arrival, consumer lag and recovery.
5. Specify reconciliation windows and watermarks so missing/extra reports do not alarm on in-flight data.

## Contracts and constraints

- Do not claim strict global ordering or effortless exactly-once delivery.
- Provide a recoverable raw source and traceable identifiers for audit.
- Distinguish business-time SLA from pipeline-processing freshness.

## Acceptance criteria

- [ ] Architecture contains explicit checkpoints, failure boundaries and recovery steps.
- [ ] Invariants are testable and ownership is clear.
- [ ] Trade-offs are explained rather than hidden behind generic architecture terminology.

## Artifacts to add **during** this session

- `docs/pipeline-design.md` and a diagram
- Test matrix and risk register

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 12: «Trading Data Pipeline Design — End-to-End QA» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/12-pipeline-design/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
