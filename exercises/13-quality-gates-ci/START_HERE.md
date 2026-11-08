# Session 13 — CI / Data Quality Gate Lab

**Focused practice:** 30–45 minutes. All discussion, review and interview feedback **in Russian**.

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
