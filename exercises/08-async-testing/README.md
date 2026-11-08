# Session 08 — Async Testing — Eventual Consistency

**Date (Asia/Bangkok):** 2026-11-10 · **Duration:** 60 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Goal

Test asynchronous processing without brittle sleeps or unbounded waits.

## Practical assignment

1. Implement a bounded `wait_until` helper using a monotonic deadline and configurable poll interval.
2. Use it to assert eventual arrival of a processed trade; report last observed state on timeout.
3. Test timeout, transient exception policy, cancellation, late success, duplicates and stale reads.
4. Discuss retry-safe reads versus unsafe repeated writes.

## Contracts and constraints

- No fixed sleep used as the sole success assertion.
- A timeout must be finite and produce actionable diagnostics.
- Poll cadence and maximum duration are explicit.

## Acceptance criteria

- [ ] Unit tests cover both successful and unsuccessful waiting.
- [ ] No infinite loop; monotonic time is used.
- [ ] Distinguishes eventual consistency from guaranteed exactly-once processing.

## Artifacts to add **during** this session

- Reusable wait helper in `src/data_qa/`
- `tests/unit/` verification and short rationale

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 08: «Async Testing — Eventual Consistency» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/08-async-testing/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
