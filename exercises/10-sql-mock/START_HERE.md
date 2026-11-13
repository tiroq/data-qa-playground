# Session 10 — Timed SQL Mock


## Unified five-block route

This session now reuses the [real optional streaming environment](../../labs/unified/README.md) and the [consolidated practice agenda](../../labs/unified/CURRICULUM.md). The older isolated exercises remain valid fallbacks if Docker/Flink is unavailable. Do not treat already supplied code as a candidate's independent answer.

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 10 — SQL Mock`  
**Session short name:** `SQL Mock`  

**Format:** 45 minutes coding without hints + 15 minutes review. All discussion and evaluation in Russian; SQL and repository code in English.

## Targeted regression after the timed phase

Use [GAP_REVIEW_CHECKLIST.md](GAP_REVIEW_CHECKLIST.md) **only after submitting the original timed answers**. Optional perturbation SQL is separate and must not change the baseline mock beforehand.

## Setup before starting the timer

```bash
docker compose up -d --wait postgres
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 < postgres/fixtures/10-sql-mock.sql
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 < postgres/checks/lab10-smoke.sql
```

The fixture **recreates only schema `lab10`**. Save your attempts before reloading it. Never reset the original Session 01/02/04 data.

When the timer starts, open [INTERVIEW_TASKS.md](INTERVIEW_TASKS.md). Preserve the original three attempts; score on correctness, required output columns, join cardinality, invalid keys, ambiguous latest versions, and timestamp eligibility. No model solutions or expected final aggregates are included.

## Post-submission reviewed SQL (do not open during timed attempt)

- [REVIEWED_SQL.sql](REVIEWED_SQL.sql): Task A latest source state, Task B logical-trade reconciliation + invalid-key report, Task C bounded 95% / 10-minute SLA. These are **reference solutions produced after review**, not the candidate's original SQL.
- [REVIEWED_CHECKS.sql](REVIEWED_CHECKS.sql): deterministic assertions and rolled-back negative controls for same-version conflict and NULL-versus-zero PnL.
- [Session 13 reviewed SQL](../13-quality-gates-ci/REVIEWED_SQL.sql): independent event-ID quality checks and an intentionally blocking fixture.

After loading the Session 10 fixture, run the reviewed SQL and regression checks **in the same connection**:

```bash
cat exercises/10-sql-mock/REVIEWED_SQL.sql exercises/10-sql-mock/REVIEWED_CHECKS.sql | docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1
```

Do not run these before the independent mock. The SQL is designed for PostgreSQL `lab10`, **not** the optional unified PostgreSQL/ClickHouse `streaming_lab`.

## Russian kickoff prompt

> Проведи строгий SQL Mock для Exness Data Stack QA полностью на русском. Прочитай INTERVIEW_TASKS.md только при старте 45-минутного таймера. Не давай подсказок до конца ответов. После этого в 15-минутном разборе оцени correctness, output completeness, NULL, JOIN cardinality, версии, SLA и сложность. Сохрани оригинальные запросы и scorecard.
