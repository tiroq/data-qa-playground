# Session 04 — Source-to-Target Reconciliation & SLA

**Date (Asia/Bangkok):** 2026-11-07 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Build a trustworthy reconciliation report that resists join multiplication and false latency alarms.

## Practical assignment

1. Define source and target grains separately; allow repeated keys on both sides in an additional **session-owned** fixture.
2. Aggregate each side at its business grain **before** joining; show a failure case for a naive many-to-many join.
3. Classify missing, orphan, duplicates, mismatched values, failed and unknown status without losing secondary flags.
4. Measure `processed_at - created_at` with an explicit eligible population, event-time cutoff and SLA: at least 95% within 10 minutes. Separate late records from an SLA breach.
5. Explain reconciliation windows, watermark, consumer lag and when a provisional missing record becomes actionable.

## Contracts and constraints

- Original Session 01 source keys are unique; construct an additional fixture to simulate duplicated source keys, rather than altering the original seed.
- Never count an outer join's fabricated null-side row as a real target record.
- SLA numerator and denominator must be defined over the same eligible cohort; no division-by-zero or null timestamp ambiguity.

## Acceptance criteria

- [ ] Cardinality checks protect the report from accidental record multiplication.
- [ ] Required columns and independent anomaly flags are complete.
- [ ] The SLA decision matches its definition on a small hand-computed example.
- [ ] Explicit policy for in-flight, late and invalid-key records.

## Artifacts to add **during** this session

- New scenario fixture, reconciliation SQL and verification assertions
- `notes/04-reconciliation-review.md` documenting edge cases

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 04: «Source-to-Target Reconciliation & SLA» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/04-reconciliation/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
