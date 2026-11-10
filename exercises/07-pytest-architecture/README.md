# Session 07 — Pytest Architecture — Fixtures & Isolation

**Date (Asia/Bangkok):** 2026-11-10 · **Duration:** 90 minutes · **Status:** COMPLETE (Session 07 lab implemented and container CI verified)  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Verified implementation (2026-11-10)

This lab is complete at the **synthetic test-system** boundary; it does not
claim access to a real Exness environment.

- **Pure Python tests:** in-memory API fake, independent event-ID delivery
  reconciliation (set + Counter), payload/version conflict checkers, expected
  empty datasets and false-green negative controls.
- **Real PostgreSQL:** session-scoped Testcontainer, function-scoped cleanup,
  READ COMMITTED two-connection isolation, explicit rollback, committed writer,
  and a nested pytest subprocess showing that a failed assertion still runs
  teardown. The test also demonstrates why using only Psycopg's connection
  context can accidentally COMMIT after a failed pytest test.
- **Real ClickHouse:** a separate Testcontainer, function-scoped database
  lifecycle, physical event history in MergeTree, a query-time latest-state
  VIEW, raw history-vs-source reconciliation, latest-but-missing-history,
  identical duplicates masking losses, mismatched PnL and same-version conflict.
- **Real HTTP:** a controlled localhost 202 Accepted service with a background
  worker, writes committed to actual PostgreSQL and ClickHouse, plus
  deterministic pause/resume, bounded source polling, processing barrier,
  timeout, corruption, dropped events and duplicate delivery.
- **Real Kafka:** Testcontainer with two partitions and real consumer commits;
  shows that `lag=0` and observing the last event are **not** sufficient
  evidence of sink durability, then compares the actual ClickHouse rows.
- **Isolation:** PostgreSQL and ClickHouse containers are per pytest worker
  session; each test gets independent IDs / ClickHouse database; worker services
  are terminated before their state is cleaned up.

**CI confirmation:**
[GitHub Actions: PostgreSQL + ClickHouse + HTTP + Kafka](https://github.com/tiroq/data-qa-playground/actions/runs/42826563119)
— both integration jobs **SUCCESS**.
[Unit/fake suite](https://github.com/tiroq/data-qa-playground/actions/runs/42826267851)
— **SUCCESS**.

[Implementation and run instructions](TEST_COVERAGE.md) lists all files,
commands, limitations and negative controls.

**Scope boundary:** the Kafka exercise uses a real broker but deliberately
manual consumer-to-sink writes; the HTTP service uses its own queue, not Kafka.
Neither is a production consumer or an externally hosted service. These are
different controlled integration boundaries, not a claim of one fully deployed
production stack.

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

- [x] A reviewer can run the selected tests repeatably (verified by two real-container CI jobs).
- [x] Cleanup occurs even on failed assertions (PostgreSQL subprocess teardown proof).
- [x] No-empty-PASS guard and failure diagnostics are demonstrated.

## Artifacts to add **during** this session

- `pyproject.toml` test configuration when introduced
- `tests/` fixtures and documented run commands

Learner approaches were reviewed first and preserved in [notes/](notes/). The subsequent full lab is now implemented and verified separately.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 07: «Pytest Architecture — Fixtures & Isolation» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/07-pytest-architecture/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** Learner's architecture reviewed in chat; the verified reference suite is committed to `main`. See `TEST_COVERAGE.md`.
- **Score / 10:** No formal timed mock interview score; architecture and code outcomes verified.
- **What worked:** transaction boundaries, SQL polling, source-of-truth assumptions, raw MergeTree + latest VIEW, set/Counter reconciliation and the Kafka lag limitation.
- **Bugs / edge cases:** ClickHouse SELECT alias collision corrected after real CI failure; Kafka Python TopicPartition property corrected; zero-row false PASS and duplicate-mask-missing covered.
- **Next-session adjustments:** Session 08 remains **PLANNED for 2026-11-11**. Its bounded-wait exercise is intentionally not solved here; the Session 07 suite uses a local illustrative polling helper.
