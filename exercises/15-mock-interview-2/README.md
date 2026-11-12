# Session 15 — Mock Interview 2 — ClickHouse, Streaming & Incident QA


**Chat title (copy to rename the conversation):** `🎯 Exness | Session 15 — Mock Interview №2`  
**Session short name:** `Mock Interview №2`  

**Date (Asia/Bangkok):** 2026-11-14 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Gap-adapted incident material

Use [INCIDENT_PACKET.md](INCIDENT_PACKET.md) in successive reveal phases and [SCORECARD_TEMPLATE.md](SCORECARD_TEMPLATE.md) only after the answer. This targets Kafka sink durability, lost events hidden by replays, ClickHouse latest-state conflicts, MV backfill and rollback. Do not expose the full packet during the first question.

## Unified Data Stack Lab alignment (2026-11-12)

**Block D — Incident Mock Interview №2.** This session is kept as a protected independent mock; no shortening. See [the five-block curriculum](../../labs/unified/CURRICULUM.md) and [the runnable stack](../../labs/unified/README.md).

- Use synthetic `streaming_lab` PostgreSQL source manifest, real Kafka/Flink SQL transport, ClickHouse raw sink and `check.py` with JSON failure evidence as the common technical case.
- Do not silently replace a candidate interview answer with prewritten code, or interpret a successful readiness smoke test as a full quality gate.
- The pre-existing exercise contracts and mock packets below remain available; no historic solutions are deleted. Calendar dates and times are **unchanged**.

## Goal

Run a scenario-driven Russian mock about production data correctness.

## Practical assignment

1. Answer ClickHouse design and troubleshooting questions on MergeTree/MV, query semantics and backfill.
2. Investigate a Kafka/Flink incident featuring retry, duplicate or reordered trades.
3. Explain a broken reconciliation/SLA dashboard and propose verification and recovery.
4. Communicate hypotheses, instrumentation, risk and a practical incident action plan.

## Contracts and constraints

- Only observed facts may be treated as certain; assumptions must be marked.
- Use Russian throughout the interview.
- Avoid pretending specific Exness internals are known.

## Acceptance criteria

- [ ] Evidence-based debugging with decision points.
- [ ] Clear mitigations and post-incident regression checks.
- [ ] Independent score and weak-topic report.

## Artifacts to add **during** this session

- `notes/15-mock-scorecard.md` and final revision targets

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 15: «Mock Interview 2 — ClickHouse, Streaming & Incident QA» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/15-mock-interview-2/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
