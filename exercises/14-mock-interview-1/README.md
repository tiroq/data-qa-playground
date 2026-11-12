# Session 14 — Mock Interview 1 — SQL, Python & Testing

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 14 — Mock Interview №1`  
**Session short name:** `Mock Interview №1`  

**Date (Asia/Bangkok):** 2026-11-13 · **Duration:** 90 minutes · **Status:** PLANNED  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Gap-adapted timed interview material

Read [MOCK_PACKET.md](MOCK_PACKET.md) only at the start of the timed mock and use [SCORECARD_TEMPLATE.md](SCORECARD_TEMPLATE.md) after submission. These cases target SQL output completeness, latest-version ambiguity and independent Python implementation from the [Sessions 01–08 audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md); no answers or solutions are prefilled.

## Unified Data Stack Lab alignment (2026-11-12)

**Block C — Independent Mock Interview №1.** This session is kept as a protected independent mock; no shortening. See [the five-block curriculum](../../labs/unified/CURRICULUM.md) and [the runnable stack](../../labs/unified/README.md).

- Use synthetic `streaming_lab` PostgreSQL source manifest, real Kafka/Flink SQL transport, ClickHouse raw sink and `check.py` with JSON failure evidence as the common technical case.
- Do not silently replace a candidate interview answer with prewritten code, or interpret a successful readiness smoke test as a full quality gate.
- The pre-existing exercise contracts and mock packets below remain available; no historic solutions are deleted. Calendar dates and times are **unchanged**.

## Goal

Run a strict Russian-language technical mock emphasizing coding and reasoning.

## Practical assignment

1. Conduct unseen SQL coding with multi-row business keys, versions and reconciliation.
2. Conduct Python exercise on comparing or polling trading data; question complexity, correctness and isolation.
3. Ask follow-ups about pytest fixtures, Testcontainers, CI and data quality.
4. Score explanations, completeness and ability to identify weak assumptions.

## Contracts and constraints

- The interviewer does not reveal a reference answer until the candidate has responded.
- Use Russian for every spoken/written discussion; keep code in its natural syntax.
- A mock attempt must preserve original answers and timing.

## Acceptance criteria

- [ ] Independent scores for SQL, Python, edge cases and communication.
- [ ] At least three prioritized gaps recorded.
- [ ] No false claim of mastery when a topic was not tested.

## Artifacts to add **during** this session

- `notes/14-mock-scorecard.md`, links to attempts and revision backlog

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 14: «Mock Interview 1 — SQL, Python & Testing» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/14-mock-interview-1/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
