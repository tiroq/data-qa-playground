# Session 09 — ClickHouse Advanced Prebuilt Lab

**Focused practice:** 60 minutes. Russian discussion and feedback; SQL and docs in English.

## Existing service

ClickHouse is already present in `compose.yaml` under the `clickhouse` profile, with `lab03.trade_versions` containing 12 physical rows and 6 logical trade keys. Do not reset or modify `lab03`.

## Prepare an isolated advanced exercise

```bash
docker compose --profile clickhouse up -d --wait clickhouse
docker compose --profile clickhouse exec -T clickhouse \
  clickhouse-client --user qa --password qa --multiquery < clickhouse/fixtures/09-advanced.sql
docker compose --profile clickhouse exec -T clickhouse \
  clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/09-advanced-smoke.sql
```

**Destructive scope:** `09-advanced.sql` intentionally drops and recreates **only `lab09`** each time. Any work you stored in `lab09` is lost; save solutions in SQL files first.

## Provided vs learner-owned

- Provided: `lab09.raw_events`, an isolated physical event copy of `lab03.trade_versions`, with initial count smoke assertions.
- Learner-owned: choose a new MV/aggregate table, define latest-version logic and conflict policy, plan backfill/migration, write quality checks and rollback.
- Do not treat `argMax`, `FINAL` or asynchronous merges as magical conflict-resolution policies.

## Design brief

Follow [BACKFILL_BRIEF.md](BACKFILL_BRIEF.md). Show a migration's checks **before** and **after**, including an intentionally replayed delivery. Explain what a ClickHouse materialized view processes at insertion time and what requires explicit backfill.

## Interview kickoff prompt

> Проведи ClickHouse Advanced как интервью на русском. Прочитай START_HERE.md, BACKFILL_BRIEF.md, схему и исходные данные. Давай одну задачу за раз, дождись моего DDL/SQL. Обязательно проверь версии, ties, backfill, TTL, replay, стоимость FINAL, правильность агрегатов и rollback. Не создавай за меня финальную MV.
