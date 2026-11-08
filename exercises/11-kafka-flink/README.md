# Session 11 — Kafka / Flink — Streaming Failure Modes

**Date (Asia/Bangkok):** 202026-11-12 **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Goal

Reason about data guarantees and test a replayable trading-event pipeline.

## Practical assignment

1. Model partitions, consumer groups, offsets, checkpointing and partition-key ordering.
2. Design tests for duplicate delivery, out-of-order events, consumer rebalances, partial failure and restart.
3. Define idempotency keys and the boundary where exactly-once can no longer be assumed.
4. Compare event time, processing time and watermark effects on reconciliation and ClickHouse writes.
5. Write a failure matrix: injection, invariant, observation, replay/recovery criterion.

## Contracts and constraints

- At-least-once input does not imply exactly-once end-to-end effects.
- Ordering is guaranteed only within the appropriate partition, not the whole topic.
- A failed consumer cannot be declared recovered solely because it reconnected.

## Acceptance criteria

- [ ] A concrete test scenario exists for each key failure mode.
- [ ] Replay yields the same logical results under the agreed contract.
- [ ] Lag, DLQ and recovery observability are specified.

## Artifacts to add **during** this session

- `docs/streaming-failure-matrix.md` and optional integration tests
- Explanation of deduplication boundaries

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 11: «Kafka / Flink — Streaming Failure Modes» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/11-kafka-flink/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
