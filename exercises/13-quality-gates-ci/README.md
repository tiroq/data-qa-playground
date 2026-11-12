# Session 13 — Quality Gates & CI — Reproducible Data Testing

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 13 — Quality Gates / CI`  
**Session short name:** `Quality Gates / CI`  

**Date (Asia/Bangkok):** 2026-11-13 · **Duration:** 60 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Unified Data Stack Lab alignment (2026-11-12)

**Block A — SQL + Quality Gates / CI.** This session shares one consolidated practice block with **Session 10**; the original session and calendar title remain valid. See [the five-block curriculum](../../labs/unified/CURRICULUM.md) and [the runnable stack](../../labs/unified/README.md).

- Use synthetic `streaming_lab` PostgreSQL source manifest, real Kafka/Flink SQL transport, ClickHouse raw sink and `check.py` with JSON failure evidence as the common technical case.
- Do not silently replace a candidate interview answer with prewritten code, or interpret a successful readiness smoke test as a full quality gate.
- The pre-existing exercise contracts and mock packets below remain available; no historic solutions are deleted. Calendar dates and times are **unchanged**.

## Goal

Make data tests actionable in CI without flaky or misleading green builds.

## Practical assignment

1. Design a GitHub Actions or GitLab CI test pipeline for SQL smoke, Python unit/integration and data contract checks.
2. Use deterministic seeds and isolated service containers; handle credentials safely.
3. Implement thresholds, explicit empty-data failure, exit codes and useful artifacts/logs.
4. Define when to block a PR versus send an operational warning; explain flaky retry policy.

## Contracts and constraints

- Do not mark success when a required test suite was skipped unexpectedly.
- CI should not depend on a developer's local volume or credentials.
- Thresholds and alert ownership are version controlled.

## Acceptance criteria

- [ ] Repeatable run instructions and visible pass/fail behavior.
- [ ] A deliberate DQ violation makes the gate fail.
- [ ] Failure evidence points to a rule, business key and evaluation window.

## Artifacts to add **during** this session

- `.github/workflows/` pipeline when implemented
- QA gate documentation and evidence from a run

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 13: «Quality Gates & CI — Reproducible Data Testing» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/13-quality-gates-ci/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
