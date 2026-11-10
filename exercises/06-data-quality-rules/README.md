# Session 06 — Data Quality — Contracts, Gates & Metrics

**Date (Asia/Bangkok):** 2026-11-09 · **Duration:** 60 minutes · **Status:** IN PROGRESS  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it now documents the runnable DQ-01 CLI, machine-readable reporting and targeted unit tests. Discuss all code and answers in Russian. **DQ-01 and DQ-02 are implemented; the full rule catalog, DQ-03, and SLA remain pending.**

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

- **Attempt / PR:** Learner DQ-01 in `starter/checkers.py` (commits `31cd8db` through `f8437b7`); runnable CLI, result model, and unit tests wired in `8168b89`. Still in progress.
- **Score / 10:** _not assessed_
- **What worked:** DQ-01 emits one explicit PASS/FAIL per nonempty cohort with per-record issues. CLI returns text/JSON, includes an input gate for empty cohorts, and does not mark unimplemented DQ rules as passing.
- **Bugs / edge cases:** Unexpectedly empty cohort now FAILs the input gate while DQ-01 remains INDETERMINATE. DQ-01 does not yet check empty string values, invalid versions, status domain, duplicates, or SLA; those are distinct future rules.
- **Verification:** GitHub Actions unit-test job succeeded on `8168b89` ([run](https://github.com/tiroq/data-qa-playground/actions/runs/42633248278)); lab readiness also succeeded ([run](https://github.com/tiroq/data-qa-playground/actions/runs/42633248275)).
- **Next-session adjustments:** DQ-02 is now integrated (commit `ca58cd3`; unit CI passed). Next: DQ-03, thresholds/denominators and late-event SLA; session is not complete.
