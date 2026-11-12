# Session 10 — Timed SQL Mock

## Consolidated learning route (2026-11-12)

**Combined meeting A: SQL & Quality Gates.** This module is studied together with **Session 13**, while retaining both original sets of exercises and chat names. Read [the five-meeting plan](../../docs/UNIFIED_FIVE_SESSION_PLAN.md) and the [unified streaming environment](../../streaming/README.md). The original session is **not marked complete**; any scored evaluation requires an actual independent answer. The shared environment can be booted using `bash scripts/streaming_lab.sh up`, but SQL-only or offline exercises do not require the heavy Flink stack.


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

## Russian kickoff prompt

> Проведи строгий SQL Mock для Exness Data Stack QA полностью на русском. Прочитай INTERVIEW_TASKS.md только при старте 45-минутного таймера. Не давай подсказок до конца ответов. После этого в 15-минутном разборе оцени correctness, output completeness, NULL, JOIN cardinality, версии, SLA и сложность. Сохрани оригинальные запросы и scorecard.
