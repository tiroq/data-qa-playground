# Session 10 — SQL Mock Interview — Correctness Under Time Pressure

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 10 — SQL Mock`  
**Session short name:** `SQL Mock`  

**Date (Asia/Bangkok):** 2026-11-11 · **Duration:** 60 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Unified Data Stack Lab alignment (2026-11-12)

**Block A — SQL + Quality Gates / CI.** This session shares one consolidated practice block with **Session 13**; the original session and calendar title remain valid. See [the five-block curriculum](../../labs/unified/CURRICULUM.md) and [the runnable stack](../../labs/unified/README.md).

- Use synthetic `streaming_lab` PostgreSQL source manifest, real Kafka/Flink SQL transport, ClickHouse raw sink and `check.py` with JSON failure evidence as the common technical case.
- Do not silently replace a candidate interview answer with prewritten code, or interpret a successful readiness smoke test as a full quality gate.
- The pre-existing exercise contracts and mock packets below remain available; no historic solutions are deleted. Calendar dates and times are **unchanged**.

## Goal

Measure SQL fluency, output completeness and time management without leading hints.

## Practical assignment

1. Complete three unseen tasks in 45 minutes: latest valid version, full reconciliation and aggregate anomaly/SLA report.
2. State assumptions and output grain up front; only ask clarifications a real interviewer could answer.
3. Use the remaining 15 minutes to audit required columns, NULL semantics, join cardinality, deterministic ties and performance.
4. Record scoring and failure causes; do not retroactively replace the submitted answer.

## Contracts and constraints

- No reference solution or answer hints until the 45-minute coding phase ends.
- All expected fields must appear, including independent flags when requested.
- The mock is scored as a time-boxed assessment, not a tutorial.

## Acceptance criteria

- [ ] Three submissions or explicit timeouts are recorded.
- [ ] Each task has a correctness and completeness evaluation.
- [ ] At least one concrete follow-up action feeds the remaining schedule.

## Artifacts to add **during** this session

- Session attempt files and `notes/10-mock-scorecard.md`

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 10: «SQL Mock Interview — Correctness Under Time Pressure» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/10-sql-mock/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
