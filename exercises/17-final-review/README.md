# Session 17 — Final Review — Confidence & Gaps

## Consolidated learning route (2026-11-12)

**Combined meeting E: Experience & Final Review.** This module is studied together with **Session 16**, while retaining both original sets of exercises and chat names. Read [the five-meeting plan](../../docs/UNIFIED_FIVE_SESSION_PLAN.md) and the [unified streaming environment](../../streaming/README.md). The original session is **not marked complete**; any scored evaluation requires an actual independent answer. The shared environment can be booted using `bash scripts/streaming_lab.sh up`, but SQL-only or offline exercises do not require the heavy Flink stack.


**Chat title (copy to rename the conversation):** `🎯 Exness | Session 17 — Final Review`  
**Session short name:** `Final Review`  

**Date (Asia/Bangkok):** 2026-11-15 · **Duration:** 60 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Targeted final drill

Use [GAP_REHEARSAL.md](GAP_REHEARSAL.md), based on the [Sessions 01–08 audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md) and later mock scorecards. This is a one-hour question-only refresher, not a new coding/infrastructure assignment.

## Unified Data Stack Lab alignment (2026-11-12)

**Block E — Experience Stories + Final Review.** This session shares one consolidated practice block with **Session 16**; the original session and calendar title remain valid. See [the five-block curriculum](../../labs/unified/CURRICULUM.md) and [the runnable stack](../../labs/unified/README.md).

- Use synthetic `streaming_lab` PostgreSQL source manifest, real Kafka/Flink SQL transport, ClickHouse raw sink and `check.py` with JSON failure evidence as the common technical case.
- Do not silently replace a candidate interview answer with prewritten code, or interpret a successful readiness smoke test as a full quality gate.
- The pre-existing exercise contracts and mock packets below remain available; no historic solutions are deleted. Calendar dates and times are **unchanged**.

## Goal

Consolidate evidence and avoid opening major new areas the day before interview.

## Practical assignment

1. Answer two brief SQL questions on latest trade state and reconciliation.
2. Review five ClickHouse/Kafka concepts with examples and failure boundaries.
3. Prepare three grounded questions for the interviewers.
4. Compile the top remaining mistakes and a concise pre-interview checklist.

## Contracts and constraints

- Do not start large new infrastructure work or claim a fully implemented system unless verified.
- Use Russian for explanations and answers.
- Prioritize clarity, correctness and confidence over novelty.

## Acceptance criteria

- [ ] A one-page revision sheet grounded in completed sessions.
- [ ] Every gap lists a next action or a deliberate accept-risk decision.
- [ ] Question list is relevant to Data Stack QA.

## Artifacts to add **during** this session

- `notes/17-final-checklist.md` after the session

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 17: «Final Review — Confidence & Gaps» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/17-final-review/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
