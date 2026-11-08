# Session 07 — Pytest Architecture — Fixtures & Isolation

**Date (Asia/Bangkok):** 2026-11-10 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Goal

Design maintainable automated tests across an API, PostgreSQL and ClickHouse.

## Practical assignment

1. Propose a layered test suite (unit, integration, data-reconciliation, end-to-end) and explain ownership and execution costs.
2. Implement fixtures with explicit scopes, cleanup, parametrization and deterministic isolation.
3. Discuss Testcontainers, database schema lifecycle, seed snapshots and CI portability.
4. Add non-vacuous assertions that fail on unexpected zero rows or unprocessed data.
5. Explain idempotence and retries for asynchronous integration tests.

## Contracts and constraints

- Production data is never required for local tests.
- A shared database fixture cannot leak state between cases.
- Use the smallest integration boundary needed to test a claim.

## Acceptance criteria

- [ ] A reviewer can run the selected tests repeatably.
- [ ] Cleanup occurs even on failed assertions.
- [ ] No-empty-PASS guard and failure diagnostics are demonstrated.

## Artifacts to add **during** this session

- `pyproject.toml` test configuration when introduced
- `tests/` fixtures and documented run commands

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 07: «Pytest Architecture — Fixtures & Isolation» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/07-pytest-architecture/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
