# Session 13 — CI / Data Quality Gate Lab

## Consolidated learning route (2026-11-12)

**Combined meeting A: SQL & Quality Gates.** This module is studied together with **Session 10**, while retaining both original sets of exercises and chat names. Read [the five-meeting plan](../../docs/UNIFIED_FIVE_SESSION_PLAN.md) and the [unified streaming environment](../../streaming/README.md). The original session is **not marked complete**; any scored evaluation requires an actual independent answer. The shared environment can be booted using `bash scripts/streaming_lab.sh up`, but SQL-only or offline exercises do not require the heavy Flink stack.


## Unified five-block route

This session now reuses the [real optional streaming environment](../../labs/unified/README.md) and the [consolidated practice agenda](../../labs/unified/CURRICULUM.md). The older isolated exercises remain valid fallbacks if Docker/Flink is unavailable. Do not treat already supplied code as a candidate's independent answer.

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 13 — Quality Gates / CI`  
**Session short name:** `Quality Gates / CI`  

**Focused practice:** 30–45 minutes. All discussion, review and interview feedback **in Russian**.

## Highest-risk negative controls

Before building a gate, read [NEGATIVE_CONTROLS.md](NEGATIVE_CONTROLS.md). This exercises missing manifests, duplicate-masks-missing, `INDETERMINATE`, skipped suites and false completion from lag=0. **Do not implement the answers automatically.**

## Prepared assets

- [GitHub Actions lab-readiness workflow](../../.github/workflows/lab-readiness.yml): fixture and environment smoke, **not a complete business quality gate**.
- [Standalone readiness tests](../../tests/labs/test_lab_readiness.py): independent of unfinished Session 05 algorithms.
- [Quality gate brief](QUALITY_GATE_BRIEF.md): explicit failure modes and required evidence.
- [Session 10 mock PostgreSQL fixture](../../postgres/fixtures/10-sql-mock.sql) and smoke check.
- [Session 09 ClickHouse smoke](../../clickhouse/checks/09-advanced-smoke.sql), optional local exercise.

## Baseline commands

```bash
uv sync --group dev
uv run pytest -q tests/labs
docker compose up -d --wait postgres
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 < postgres/checks/smoke.sql
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 < postgres/fixtures/10-sql-mock.sql
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 < postgres/checks/lab10-smoke.sql
```

The SQL fixture reload is destructive **only to lab10**. The preparatory workflow deliberately does not run unfinished Session 05 reconciliation nor assert ClickHouse/Kafka/Flink features as complete.

## Interview task

Develop a real CI DQ gate from these starting checks. Define blocking thresholds, active/testable input cohorts, one deliberately failing DQ fixture, no-empty-PASS, error codes and diagnostic artifacts. Separate per-record anomalies from SLA cohort failure, and distinguish infrastructure errors from business defects.

> Проведи интервью по quality gates на русском. Прочитай START_HERE.md, QUALITY_GATE_BRIEF.md и исходный workflow. Сначала попроси меня предложить улучшения, потом выясняй, как я докажу провал проверки при нарушении DQ, пустом датасете и пропущенном тесте. Не называй smoke-тест доказательством бизнес-корректности.
