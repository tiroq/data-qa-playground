# Session 09 — ClickHouse Advanced: Conversational Architecture Review

**Date (Asia/Bangkok):** 2026-11-11 · **Default duration:** 60 minutes · **Status:** PLANNED / oral-first  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language:** All discussion, interview questions, reasoning, code review and feedback take place **in Russian**. Technology names and SQL syntax may remain in English. GitHub materials are written in English.

## Format — theory first, implementation only from discussion

This session is now an **interactive technical interview**, not a mandatory SQL live-coding lab. We use the prebuilt synthetic ClickHouse case, discuss assumptions and compare architectures, then record the conclusions. Only SQL/DDL examples that are **actually discussed and approved** are added afterward as separate artifacts. Do not fill in alternative answers or mark the session complete in advance.

**Start here:** [THEORY_SESSION.md](THEORY_SESSION.md) (interview flow), [SCENARIO_CARDS.md](SCENARIO_CARDS.md) (progressive cases), [DECISION_MATRIX.md](DECISION_MATRIX.md) (comparison template), [discussions/README.md](discussions/README.md) (capturing evidence), [START_HERE.md](START_HERE.md) (optional runnable fixture).

## Learning objective

Defend a trading-data quality design in ClickHouse under duplicate delivery, version updates, asynchronous merges, conflicts, backfill, materialized views, TTL and rollback. Explain **what is guaranteed**, what is merely a design assumption, and which test would falsify a claim.

## Conversation agenda (60 minutes)

| Time | Topic | Interview challenge |
|---|---|---|
| 0–10 min | Storage semantics | MergeTree, ReplacingMergeTree, physical vs logical records, FINAL |
| 10–25 min | Latest state and aggregates | argMax, same-version ties, PnL correctness and raw-vs-view reconciliation |
| 25–40 min | Materialized views and replay | Insert-time behavior, MV target choice, idempotency and historical backfill |
| 40–50 min | Migration, TTL and rollback | Shadow validation, cutover, retention and recoverability |
| 50–60 min | Interview follow-ups | Distributed limitations, failure diagnosis, score and three learning gaps |

The interviewer may spend extra time on one difficult case and skip lower-priority topics; record what was actually covered.

## Grounded synthetic case

- Existing `lab03.trade_versions`: **12 physical deliveries** for **6 logical business keys**.
- Repeated version-2 payload: trade **201**.
- Older version arrives later than newer: trade **203**.
- Two conflicting maximum-version PnL values: trade **205**.
- Nullable PnL/status: trade **204**.
- Optional `lab09.raw_events` fixture is an isolated copy of this history. It is **not required** to start oral discussion.

Use source data and schema as evidence, not invented production behavior. [BACKFILL_BRIEF.md](BACKFILL_BRIEF.md) remains the optional hands-on extension.

## Conversational success criteria

- [ ] Candidate distinguishes physical rows, logical trades, immutable events, versions and time windows.
- [ ] Candidate compares at least two viable storage/view strategies, with operational risks and QA checks.
- [ ] A same-version conflict is not resolved by accidental row ordering.
- [ ] Candidate specifies how to detect false aggregate correctness after duplicate/replayed deliveries.
- [ ] Candidate explains a feasible backfill, cutover and rollback plan and its limits.
- [ ] Notes clearly separate **candidate answer**, **reviewer's challenge**, **agreed conclusion** and **unverified claim**.
- [ ] Three targeted follow-ups are recorded. No claims of PASS or executed SQL unless actually verified.

## Optional implementation backlog — NOT required today

Only after discussion, implement selected design choices from the original brief:

1. Target table, possible materialized view and explicit version-conflict policy.
2. Query-level comparison for raw history vs latest state / account-level PnL.
3. Safe backfill or shadow migration with before/after assertions and replay scenario.
4. Retention, schema evolution and rollback checks.

Save reviewed examples under `discussions/` as Markdown first, and only create SQL files under `solutions/` after their logic is decided. Keep source `clickhouse/init/` and original `lab03` unchanged.

## Standalone ChatGPT kickoff prompt (Russian)

> Проводи **Session 09 — ClickHouse Advanced** как устное техническое интервью по Data Stack QA на русском языке, продолжительностью до 60 минут. Прочитай `exercises/09-clickhouse-advanced/THEORY_SESSION.md`, `SCENARIO_CARDS.md`, `DECISION_MATRIX.md` и исходные данные из `clickhouse/init/02-seed.sql` в `tiroq/data-qa-playground`. Давай **один кейс или вопрос за раз**, жди моего ответа, затем выявляй слабые допущения, предлагай контрпример и задавай follow-up. Не требуй написания SQL/DDL в ходе разговора и не показывай эталон заранее. После обсуждения записывай в репозиторий только рассмотренные кейсы, мои реальные аргументы, подтверждённые выводы и открытые вопросы. Реализацию добавляй лишь когда мы отдельно решим её делать. В конце оценка /10 и три приоритета для повторения.

## Session result (fill only after discussion)

**Status:** not yet assessed. See [discussion record template](DISCUSSION_RECORD_TEMPLATE.md); score and verification evidence remain unset until actual conversation.
