# Session 06 — Data Quality — Contracts, Gates & Metrics

**Date (Asia/Bangkok):** 2026-11-08 · **Duration:** 60 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Translate trading-data expectations into measurable, automatable quality checks.

## Practical assignment

1. Specify at least ten non-overlapping DQ rules across completeness, uniqueness, validity, consistency, freshness and reconciliation.
2. For each rule define dataset grain, query or test strategy, evaluation window, owner, severity and explicit threshold.
3. Separate per-record anomalies from aggregate SLO/SLA breach criteria; demonstrate the distinction with sample percentages.
4. Design alerting and quarantine decisions for invalid keys, failed processing, duplicates and late data.

## Contracts and constraints

- Quality thresholds are scenario assumptions, not Exness internal policy.
- A rule must not produce a vacuous PASS when the evaluation dataset is unexpectedly empty.
- Late events require a documented evaluation cutoff.

## Acceptance criteria

- [ ] Every rule is machine-verifiable and includes the denominator when applicable.
- [ ] A false-positive case and a false-negative case are discussed.
- [ ] Blocking and nonblocking checks have clear semantics.

## Artifacts to add **during** this session

- `docs/data-quality-rules.md` with rule catalog after practice
- Targeted unit/SQL tests where appropriate

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 06: «Data Quality — Contracts, Gates & Metrics» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/06-data-quality-rules/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
