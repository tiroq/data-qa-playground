# ClickHouse local lab — Session 03

This is a **synthetic**, local-only fixture for [Session 03](../exercises/03-clickhouse-fundamentals/README.md). It is intentionally NOT a deduplication reference implementation.

## Start only ClickHouse (does not require PostgreSQL)

```bash
docker compose --profile clickhouse up -d --wait clickhouse
docker compose --profile clickhouse ps
docker compose --profile clickhouse exec clickhouse clickhouse-client --user qa --password qa --database lab03
```

The first startup with a **new** `clickhouse_data` volume runs `init/01-schema.sql` followed by `init/02-seed.sql` through the image's init-directory mechanism. Data persists across container restarts. PostgreSQL and its historical fixtures are unchanged.

At the ClickHouse prompt:

```sql
SHOW TABLES FROM lab03;
DESCRIBE TABLE lab03.trading_events;
SELECT * FROM lab03.trading_events ORDER BY ingest_id;
SELECT * FROM lab03.trade_versions ORDER BY ingest_id;
```

`SELECT version();` prints the running server version. Exit with `exit` or Ctrl-D.

## Verify raw fixtures

From the repository root:

```bash
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/smoke.sql
```

Checks fail if expected raw counts or business-key counts are wrong. They deliberately **do not** assert a latest-state PnL or leak a deduplication solution.

| Table | Physical rows | Logical keys | Purpose |
| --- | ---: | ---: | --- |
| `lab03.trading_events` | 6 | 3 | Small Session 03 interview case with duplicate delivery and changed PnL |
| `lab03.trade_versions` | 12 | 6 | Session 02 PostgreSQL fixture reproduced in ClickHouse: replay, late arrival, NULL and same-version conflict |

**Important:** Both input tables use plain `MergeTree` and retain physical rows. They are not proposed final business tables. As an exercise, design a separate `ReplacingMergeTree(version)` table, choose its sorting and partition keys, load it with `INSERT ... SELECT`, and investigate `FINAL` and merge timing. Do not overwrite raw fixtures. A plain `MergeTree` merge does **not** remove logical duplicates. Do not use `OPTIMIZE FINAL` as a normal production dedup strategy.

## Connect external SQL clients

- Host: `127.0.0.1` (localhost only)
- HTTP port: `18123`
- Native port: `19000`
- Database: `lab03`
- User: `qa`; password: `qa` (local lab only)

Supported image tag is pinned to `clickhouse/clickhouse-server:26.8.36.3`, which has both amd64 and arm64 images.

## Deliberate fixture reload (destructive ONLY for these two ClickHouse tables)

Use this only to discard changes to the two **raw input tables** and restore their initial content. This does not drop your separately named exercise tables, and does not modify PostgreSQL.

```bash
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --query 'TRUNCATE TABLE lab03.trading_events'
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --query 'TRUNCATE TABLE lab03.trade_versions'
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --multiquery < clickhouse/init/02-seed.sql
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/smoke.sql
```

The seed file uses plain INSERTs. **Never rerun it without truncating first:** ClickHouse does not enforce uniqueness of `ingest_id` in these raw tables.

## Practice sequence (no answers)

1. Count physical rows and logical trades, then calculate PnL without filtering versions.
2. Propose and implement your own replacement table, including `ORDER BY`, `PRIMARY KEY` if different, and `PARTITION BY`.
3. Compare actual results before and after deduplication, including query-time `FINAL`; explain when a merge may or may not run.
4. Investigate delayed ingest, same-version replay, and contradictory same-version data in `trade_versions`.
5. Record your SQL, test output, and trade-offs in `exercises/03-clickhouse-fundamentals/` after attempting the exercises.

**Verification status:** the repository contains setup, deterministic expected counts, and smoke SQL; a local Docker execution and observed checks have **not** been run or claimed by this commit.
