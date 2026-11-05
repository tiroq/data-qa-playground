# Session 05 — Python Live Coding — Streaming Comparison

**Date (Asia/Bangkok):** 2026-11-08 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Implement Python comparison primitives for trading data and explain space/time trade-offs.

## Practical assignment

1. Define typed inputs and outputs for source-vs-target comparison keyed by `(trade_id, account_id)` and version/event id.
2. Identify missing, extra, changed, duplicate and malformed rows without quietly discarding invalid input.
3. Use `Decimal` for monetary values; specify comparison tolerance policy if any.
4. Choose an algorithm for both small in-memory and larger sorted/streaming datasets, state complexity and failure modes.
5. Write parameterized tests for empty sets, one-to-many, stale versions, nullable keys and stable ordering.

## Contracts and constraints

- Never silently interpret a processing attempt as a unique trade.
- Do not mix transport duplicate delivery with business lifecycle changes.
- Provide deterministic failure reports with enough identifiers for debugging.

## Acceptance criteria

- [ ] Pure comparison logic is testable without external services.
- [ ] Time/space complexity and mutation safety are explained.
- [ ] At least five meaningful edge-case tests.

## Artifacts to add **during** this session

- `src/data_qa/` Python implementation introduced during this session
- `tests/unit/` tests and `notes/05-python-review.md`

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 05: «Python Live Coding — Streaming Comparison» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/05-python-live-coding/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
